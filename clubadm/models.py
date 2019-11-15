import datetime
import logging

from django.conf import settings
from django.contrib import auth
from django.core.cache import cache
from django.db import models, connection
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property

from clubadm.tasks import send_notification


logger = logging.getLogger(__name__)


def _get_mails_cache_key(member1, member2):
    # Чтобы один участник мог использовать кэш другого, сортируем параметры
    # ключа в порядке возрастания ID, независимо от порядка аргументов.
    return "mails:%d:%d" % tuple(sorted([member1.id, member2.id]))


class SeasonManager(models.Manager):
    def get_queryset(self):
        return super(SeasonManager, self).get_queryset().annotate(
            members=models.Count("member", distinct=True),
            sent=models.Count("member__gift_sent", distinct=True),
            received=models.Count("member__gift_received", distinct=True))

    def get_by_year(self, year):
        season_key = "season:%d" % int(year)
        season = cache.get(season_key)
        if not season:
            season = self.get(pk=year)
            cache.set(season_key, season, timeout=None)
        return season


class Season(models.Model):
    year = models.IntegerField("год", primary_key=True)
    gallery = models.URLField("пост хвастовства подарками", blank=True)
    signups_start = models.DateField("начало регистрации")
    signups_end = models.DateField("жеребьевка адресов")
    ship_by = models.DateField("последний срок отправки подарка", help_text=
                               "После этой даты сезон закрывается и уходит в"
                               "архив.")

    objects = SeasonManager()

    class Meta:
        ordering = ["year"]
        get_latest_by = "year"
        verbose_name = "сезон"
        verbose_name_plural = "сезоны"

    def __str__(self):
        return "АДМ-%d" % self.year

    @property
    def cache_key(self):
        return "season:%d" % self.pk

    def save(self, *args, **kwargs):
        super(Season, self).save(*args, **kwargs)
        cache.set(self.cache_key, self, timeout=None)

    def delete(self, *args, **kwargs):
        super(Season, self).delete(*args, **kwargs)
        cache.delete(self.cache_key)

    def get_absolute_url(self):
        return '/%d/' % self.year

    @property
    def is_closed(self):
        return timezone.now().date() > self.ship_by

    @property
    def is_participatable(self):
        today = timezone.now().date()
        return today >= self.signups_start and today < self.signups_end


class UserManager(models.Manager):
    def get_by_id(self, user_id):
        user_key = "user:%d" % int(user_id)
        user = cache.get(user_key)
        if not user:
            user = self.get(pk=user_id)
            cache.set(user_key, user, timeout=None)
        return user


class User(models.Model):
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_UNKNOWN = 0

    BADGE_ID = 1018

    username = models.CharField("имя пользователя", max_length=25, unique=True)
    access_token = models.CharField("токен доступа", blank=True, max_length=40)
    is_oldfag = models.BooleanField("старый участник", default=False, help_text=
                                    "Отметьте, чтобы снять ограничение кармы.")
    is_banned = models.BooleanField("забанен", default=False)
    first_login = models.DateTimeField("первый вход", default=timezone.now)
    last_login = models.DateTimeField("последний вход", blank=True, null=True)

    is_anonymous = False
    is_authenticated = True

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["username"]
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.was_banned = self.is_banned

    def __str__(self):
        return self.username

    @property
    def cache_key(self):
        return "user:%d" % self.id

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        cache.set(self.cache_key, self, timeout=None)
        if not self.was_banned and self.is_banned:
            logger.debug("Пользователь %s забанен", self.username)
            self.send_notification("Ваш аккаунт заблокирован",
                                   "clubadm/notifications/banned.html")
        elif self.was_banned and not self.is_banned:
            logger.debug("Пользователь %s разбанен", self.username)
            self.send_notification("Ваш аккаунт разблокирован",
                                   "clubadm/notifications/unbanned.html")

    def delete(self, *args, **kwargs):
        super(User, self).delete(*args, **kwargs)
        cache.delete(self.cache_key)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def get_username(self):
        return self.username

    @property
    def is_admin(self):
        return settings.DEBUG or self.username in settings.CLUBADM_ADMINS

    @cached_property
    def remote(self):
        remote = dict()
        for backend in auth.get_backends():
            if not hasattr(backend, "get_remote_user"):
                continue
            try:
                remote.update(
                    backend.get_remote_user(self.access_token))
            except:
                pass
        return remote

    @property
    def avatar(self):
        default = "https://habrahabr.ru/i/avatars/stub-user-middle.gif"
        return self.remote.get("avatar", default)

    @property
    def karma(self):
        return float(self.remote.get("score", 0.0))

    @property
    def rating(self):
        return float(self.remote.get("rating", 0.0))

    @property
    def gender(self):
        return self.remote.get("sex", self.GENDER_UNKNOWN)

    @property
    def is_male(self):
        return self.gender == self.GENDER_MALE

    @property
    def is_female(self):
        return self.gender == self.GENDER_FEMALE

    @property
    def is_readcomment(self):
        return self.remote.get("is_rc", True)

    @property
    def is_readonly(self):
        return self.remote.get("is_readonly", True)

    @property
    def has_badge(self):
        badges = self.remote.get("badges")
        if not badges:
            return False
        for badge in badges:
            if badge.get("id") == self.BADGE_ID:
                return True
        return False

    @property
    def can_participate(self):
        invited = not self.is_readonly and not self.is_readcomment
        good_guy = self.is_oldfag or self.has_badge
        return not self.is_banned and invited and (good_guy or
            self.karma >= settings.CLUBADM_KARMA_LIMIT)

    def send_notification(self, title, template_name, context=None):
        text = render_to_string(template_name, context)
        logger.debug("Отправляю уведомление: title=%s, text=%s", title, text)
        send_notification.delay(self.access_token, title, text)


class MemberManager(models.Manager):
    def get_by_user_and_year(self, user, year):
        # FIXME(kafeman): ORM в Django писали какие-то криворукие уроды, поэтому
        # мы не можем получить АДМ и АПП в одном запросе, даже через RawSQL,
        # потому что эти дебилы не могут правильно распарсить готовый результат.
        queryset = self.select_related("giftee").prefetch_related("santa")
        return queryset.get(user=user, season_id=year)


class Member(models.Model):
    user = models.ForeignKey(User, verbose_name="пользователь")
    season = models.ForeignKey(Season, verbose_name="сезон")
    giftee = models.OneToOneField("self", related_name="santa",
                                  verbose_name="получатель подарка",
                                  blank=True, null=True)
    fullname = models.CharField("полное имя", max_length=80)
    postcode = models.CharField("индекс", max_length=20)
    address = models.TextField("адрес", max_length=200)
    gift_sent = models.DateTimeField("подарок отправлен", db_index=True,
                                     blank=True, null=True)
    gift_received = models.DateTimeField("подарок получен", db_index=True,
                                         blank=True, null=True)

    objects = MemberManager()

    class Meta:
        verbose_name = "участник"
        verbose_name_plural = "участники"
        ordering = ["season", "fullname"]
        unique_together = ("user", "season")

    def __str__(self):
        return "%s (%s)" % (self.fullname, self.season)

    @property
    def is_gift_sent(self):
        return self.gift_sent is not None

    @property
    def is_gift_received(self):
        return self.gift_received is not None

    def read_mails(self, sender, timestamp):
        Mail.objects.filter(
            sender=sender,
            recipient=self,
            read_date__isnull=True,
            send_date__lte=timezone.make_aware(datetime.datetime.fromtimestamp(timestamp)),
            send_date__gte=timezone.make_aware(datetime.datetime(2016, 12, 20))
        ).update(read_date=timezone.now())
        cache.delete(_get_mails_cache_key(self, sender))

    def send_mail(self, body, recipient):
        mail = Mail(body=body, sender=self, recipient=recipient)
        mail.save()

    def send_gift(self):
        self.gift_sent = timezone.now()
        self.save()

    def receive_gift(self):
        self.gift_received = timezone.now()
        self.save()


class MailManager(models.Manager):
    def get_between(self, member1, member2):
        mails_key = _get_mails_cache_key(member1, member2)
        mails = cache.get(mails_key)
        if not mails:
            mails = list(self.filter(
                models.Q(sender=member1, recipient=member2) |
                models.Q(recipient=member1, sender=member2)
            ))
            cache.set(mails_key, mails, timeout=None)
        return mails


class Mail(models.Model):
    body = models.TextField(max_length=400)
    sender = models.ForeignKey(Member, related_name="+")
    recipient = models.ForeignKey(Member, related_name="+")
    send_date = models.DateTimeField(default=timezone.now, db_index=True)
    read_date = models.DateTimeField(blank=True, null=True, db_index=True)

    objects = MailManager()

    class Meta:
        ordering = ["send_date"]

    def save(self, *args, **kwargs):
        super(Mail, self).save(*args, **kwargs)
        cache.delete(_get_mails_cache_key(self.sender, self.recipient))

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.db import models, connection
from django.db.models import Count
from django.http import Http404
from django.utils import timezone
from django.utils.functional import cached_property

from clubadm.tasks import send_notification


GENDER_MALE = 1
GENDER_FEMALE = 2
GENDER_UNKNOWN = 0


class SeasonManager(models.Manager):
    def get_queryset(self):
        return super(SeasonManager, self).get_queryset().annotate(
            members=Count('member', distinct=True),
            sent=Count('member__gift_sent', distinct=True),
            received=Count('member__gift_received', distinct=True))

    def get_by_year(self, year):
        if year == 'latest':
            return self.latest()
        return self.get(year=year)


class Season(models.Model):
    year = models.IntegerField(
        'год', default=timezone.now().year, primary_key=True)
    gallery = models.URLField('пост хвастовства подарками', blank=True)
    signups_start = models.DateField('начало регистрации')
    signups_end = models.DateField('жеребьевка адресов')
    ship_by = models.DateField(
        'последний срок отправки подарка',
        help_text='После этой даты сезон закрывается и уходит в архив.')

    objects = SeasonManager()

    class Meta:
        ordering = ('year',)
        get_latest_by = 'year'
        verbose_name = 'сезон'
        verbose_name_plural = 'сезоны'

    def __str__(self):
        return 'АДМ-%d' % self.year

    def is_closed(self):
        """Возвращает True, если сезон находится в архиве.

        Информация из сезонов, помещенных в архив, допуступна только для чтения.
        Сезон попадает в архив после истечения отведенного на отправку срока.
        """
        return timezone.now().date() > self.ship_by
    is_closed.boolean = True
    is_closed.short_description = 'сезон завершен'

    def is_participatable(self):
        """Возвращает True, если регистрация новых участников еще возможна.

        Регистрация закрывается после того, как адреса розданы. Данный метод не
        берет в расчет конкретного пользователя. См. Profile.can_participate.
        """
        today = timezone.now().date()
        return today >= self.signups_start and today < self.signups_end
    is_participatable.boolean = True
    is_participatable.short_description = 'регистрация открыта'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_oldfag = models.BooleanField(
        'старый участник', default=False,
        help_text='Отметьте, чтобы снять ограничение кармы.')
    access_token = models.CharField(
        'токен доступа', blank=True, max_length=40,
        help_text='Токен для доступа к API Хабрахабра/Geektimes.')

    @cached_property
    def _service_profile(self):
        """Возвращает профиль, хранящийся на серверах ТМ."""
        service_profile = dict()
        for backend in auth.get_backends():
            if not hasattr(backend, 'get_service_profile'):
                continue
            try:
                service_profile.update(
                    backend.get_service_profile(self.access_token))
            except:
                pass
        return service_profile

    def avatar(self):
        return self._service_profile.get(
            'avatar', 'https://habrahabr.ru/i/avatars/stub-user-middle.gif')
    avatar.short_description = 'аватарка'

    def karma(self):
        return self._service_profile.get('score', 0.0)
    karma.short_description = 'карма'

    def rating(self):
        return self._service_profile.get('rating', 0.0)
    rating.short_description = 'рейтинг'

    def gender(self):
        return self._service_profile.get('sex', GENDER_UNKNOWN)
    gender.short_description = 'пол'

    def is_male(self):
        return self.gender() == GENDER_MALE
    is_male.boolean = True
    is_male.short_description = 'мужчина'

    def is_female(self):
        return self.gender() == GENDER_FEMALE
    is_female.boolean = True
    is_female.short_description = 'женщина'

    def is_readcomment(self):
        return self._service_profile.get('is_rc', True)
    is_readcomment.boolean = True
    is_readcomment.short_description = 'R&C'

    def is_readonly(self):
        return self._service_profile.get('is_readonly', True)
    is_readonly.boolean = True
    is_readonly.short_description = 'молчун'

    def can_participate(self):
        """Может ли пользователь принимать участие в новых сезонах.

        Обсудить формулу можно в этой ветке на Хабрахабре:
        http://habrahabr.ru/post/246473/#comment_8200973

        Данный метод не берет в расчет конкретный сезон.
        """
        invited = not self.is_readonly() and not self.is_readcomment()
        return self.user.is_active and invited and (self.is_oldfag or
            self.karma() >= settings.CLUBADM_KARMA_LIMIT)
    can_participate.boolean = True
    can_participate.short_description = 'может участвовать'

    def send_notification(self, title, text):
        """Отправить пользователю уведомление в трекер.

        Фактическая отправка не производится, только создается новая задача.
        """
        send_notification.delay(self.access_token, title, text)


class MemberManager(models.Manager):
    def get_by_user_and_year(self, user_id, year):
        """Возвращает модель участника или бросает исключение Http404.

        Продолжаем портировать запросы из старого движка на ORM. Сгенерировать
        похожий запрос Django 1.9 может, но при попытке разобрать его валится с
        ошибкой (как показывает отладка, Django не понимает, что делать с такой
        кучей данных). Времени разбираться не было, поэтому скопировал старый
        запрос почти без изменений (добавив только новую таблицу profile).

        TODO(kafeman): Отправить багрепорт разработчикам этого недо-ORM.
        TODO(kafeman): Создать Клуб анонимных любителей LEFT OUTER JOIN.
        """
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                -- участник
                m.id, m.user_id, m.season_id, m.giftee_id, m.fullname,
                m.postcode, m.address, m.last_visit, m.gift_sent,
                m.gift_received,
                -- сезон
                ms.year, ms.gallery, ms.signups_start, ms.signups_end,
                ms.ship_by,
                -- получатель подарка
                g.id, g.user_id, g.season_id, g.giftee_id, g.fullname,
                g.postcode, g.address, g.last_visit, g.gift_sent,
                g.gift_received,
                -- аккаунт получателя подарка
                gu.id, gu.password, gu.last_login, gu.is_superuser, gu.username,
                gu.first_name, gu.last_name, gu.email, gu.is_staff,
                gu.is_active, gu.date_joined,
                -- профиль получателя подарка
                gp.id, gp.user_id, gp.is_oldfag, gp.access_token,
                -- Дед Мороз
                s.id, s.user_id, s.season_id, s.giftee_id, s.fullname,
                s.postcode, s.address, s.last_visit, s.gift_sent,
                s.gift_received,
                -- аккаунт Деда Мороза
                su.id, su.password, su.last_login, su.is_superuser, su.username,
                su.first_name, su.last_name, su.email, su.is_staff,
                su.is_active, su.date_joined,
                -- профиль Деда Мороза
                sp.id, sp.user_id, sp.is_oldfag, sp.access_token
            FROM
                clubadm_member AS m
                LEFT OUTER JOIN auth_user AS mu ON m.user_id = mu.id
                LEFT OUTER JOIN clubadm_season AS ms ON m.season_id = ms.year
                LEFT OUTER JOIN clubadm_member AS g ON m.giftee_id = g.id
                LEFT OUTER JOIN auth_user AS gu ON g.user_id = gu.id
                LEFT OUTER JOIN clubadm_profile AS gp ON gp.user_id = gu.id
                LEFT OUTER JOIN clubadm_member AS s ON s.giftee_id = m.id
                LEFT OUTER JOIN auth_user AS su ON s.user_id = su.id
                LEFT OUTER JOIN clubadm_profile AS sp ON sp.user_id = su.id
            WHERE
                m.user_id = %s AND m.season_id = %s""", [user_id, year])

        # Как показывает traceback, вот на этом Django и валится.
        row = cursor.fetchone()
        if not row or row[0] is None:
            raise Http404('Пользователь не участвует в сезоне.')
        member = Member(*row[0:10])
        member.season = Season(*row[10:15])
        if row[15] is not None:
            member.giftee = Member(*row[15:25])
            member.giftee.user = User(*row[25:36])
            member.giftee.user.profile = Profile(*row[36:40])
        else:
            member.giftee = None
        if row[40] is not None:
            member.santa = Member(*row[40:50])
            member.santa.user = User(*row[50:61])
            member.santa.user.profile = Profile(*row[61:65])
        else:
            member.santa = None

        return member


class Member(models.Model):
    user = models.ForeignKey(User, verbose_name='пользователь')
    season = models.ForeignKey(Season, verbose_name='сезон')
    giftee = models.OneToOneField('self', blank=True, null=True,
                                  related_name='santa',
                                  verbose_name='получатель подарка')
    fullname = models.CharField('полное имя', max_length=200, db_index=True)
    postcode = models.CharField('индекс', max_length=20)
    address = models.TextField('адрес', max_length=500)
    last_visit = models.DateTimeField('последний визит', default=timezone.now)
    gift_sent = models.DateTimeField('подарок отправлен', db_index=True,
                                     blank=True, null=True)
    gift_received = models.DateTimeField('подарок получен', db_index=True,
                                         blank=True, null=True)

    objects = MemberManager()

    class Meta:
        verbose_name = 'участник'
        verbose_name_plural = 'участники'
        ordering = ('season', 'fullname')

    def __str__(self):
        return '%s (%s)' % (self.fullname, self.season)

    def is_gift_sent(self):
        return self.gift_sent is not None
    is_gift_sent.boolean = True
    is_gift_sent.short_description = 'подарок отправлен'

    def is_gift_received(self):
        return self.gift_received is not None
    is_gift_received.boolean = True
    is_gift_received.short_description = 'подарок получен'

    def send_notification(self, title, text):
        self.user.profile.send_notification(title, text)


class Mail(models.Model):
    sender = models.ForeignKey(Member, related_name='+')
    recipient = models.ForeignKey(Member, related_name='+')
    body = models.TextField(max_length=400)
    sent = models.DateTimeField(db_index=True, default=timezone.now)

    class Meta:
        ordering = ('sent',)

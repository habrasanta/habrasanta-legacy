import json
import logging
import requests

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import urlencode

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import detail_route, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clubadm.models import Season, Member, Mail
from clubadm.serializers import SeasonSerializer, MemberSerializer, ChatSerializer


logger = logging.getLogger(__name__)


def home(request):
    jsdata = {
        'user': None,
        'security': {
            'token': get_token(request),
        },
        'partials': {
            'season': staticfiles_storage.url('season.html'),
            'welcome': staticfiles_storage.url('welcome.html'),
            'profile': staticfiles_storage.url('profile.html'),
        },
    }
    if request.user.is_authenticated():
        jsdata['user'] = {
            'username': request.user.username,
            'avatar': request.user.profile.avatar(),
            'is_active': request.user.is_active,
            'can_participate': request.user.profile.can_participate(),
        }
    return render(request, 'clubadm/index.html', {
        'jsdata': json.dumps(jsdata, separators=(',', ':'))
    })


def oldprofile(request, year=None):
    if year:
        return redirect('/#/%s/profile' % year)
    # В 2012 г. данные аутентификации хранились в параметре hash.
    if 'hash' in request.GET:
        return redirect('/#/2012/profile')
    return redirect('/#/2013/profile')


def login(request):
    redirect_uri = '%s?%s' % (reverse('callback'), urlencode({
        'next': request.GET.get('next', reverse('home'))
    }))
    return redirect('%s?%s' % (settings.TMAUTH_LOGIN_URL, urlencode({
        'client_id': settings.TMAUTH_CLIENT,
        'response_type': 'code',
        'redirect_uri': request.build_absolute_uri(redirect_uri),
    })))


def callback(request):
    error = request.GET.get('error')
    if error:
        logger.error('Не удалось получить code: %s.', error)
        return redirect(reverse('home'))

    response = requests.post(settings.TMAUTH_TOKEN_URL, data = {
        'grant_type': 'authorization_code',
        'code': request.GET.get('code'),
        'client_id': settings.TMAUTH_CLIENT,
        'client_secret': settings.TMAUTH_SECRET
    })
    response.raise_for_status()

    user = authenticate(access_token=response.json().get('access_token'))
    auth_login(request, user)

    # FIXME(kafeman): Если next содержит полный путь, а response_type был
    # изменен на token, то токен утечет на внешний сайт. Но всем как всегда...
    redirect_to = request.GET.get('next', reverse('home'))
    return redirect(redirect_to)


class SeasonViewSet(viewsets.ViewSet):
    """Обработчик всех AJAX-запросов."""
    def retrieve(self, request, pk=None):
        season = self.get_season(pk)
        serializer = SeasonSerializer(season)
        return Response(serializer.data)

    @detail_route(methods=['get'], permission_classes=[IsAuthenticated])
    def member(self, request, pk=None):
        """Возвращает информацию об участнике.

        TODO(kafeman): Объединить с retrieve.
        """
        member = self.get_member(request, pk)
        serializer = MemberSerializer(member)
        return Response(serializer.data)

    @detail_route(methods=['get'], permission_classes=[IsAuthenticated])
    def chat(self, request, pk=None):
        """Возвращает сообщения из чата.

        TODO(kafeman): Объединить с retrieve.
        """
        member = self.get_member(request, pk)
        mails = self.get_mails(member)

        serializer = ChatSerializer(mails, context={
            'member': member
        })
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def send_mail(self, request, pk=None):
        """Отправляет письмо в чатик."""
        member = self.get_member(request, pk)

        if member.season.is_closed():
            raise ValidationError('Сезон перенесен в архив.')

        body = request.data.get('body', '').strip()
        if not body:
            raise ValidationError('Вначале нужно что-то написать.')

        recipient = request.data.get('recipient')
        if recipient == 'giftee':
            if not member.giftee:
                raise ValidationError('У вас нет АПП.')
            member.giftee.send_notification(
                'Новое сообщение от Деда Мороза',
                render_to_string('clubadm/notification_santa_mail.html', {
                    'season': member.season
                }))
            mail = Mail(body=body, sender=member, recipient=member.giftee)
            mail.save()
            self.delete_mails_cache(member)
            self.delete_mails_cache(member.giftee)
        else:
            if not member.santa:
                raise ValidationError('У вас нет АДМ.')
            member.santa.send_notification(
                'Новое сообщение от получателя подарка',
                render_to_string('clubadm/notification_giftee_mail.html', {
                    'season': member.season
                }))
            mail = Mail(body=body, sender=member, recipient=member.santa)
            mail.save()
            self.delete_mails_cache(member)
            self.delete_mails_cache(member.santa)

        mails = self.get_mails(member)
        serializer = ChatSerializer(mails, context={
            'member': member
        })

        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def send_gift(self, request, pk=None):
        """Отмечает, что участник отправил подарок."""
        member = self.get_member(request, pk)

        if member.season.is_closed():
            raise ValidationError('Сезон перенесен в архив.')

        if not member.giftee:
            raise ValidationError('У вас нет АПП.')

        if member.is_gift_sent():
            raise ValidationError('Подарок уже отправлен.')
        member.gift_sent = timezone.now()
        member.giftee.send_notification(
            'Вам отправлен подарок',
            'Пожалуйста, не забудьте отметить его получение.')
        member.save()

        cache.delete_many([
            'member_%d_%s' % (member.user.id, pk),
            'member_%d_%s' % (member.giftee.user.id, pk),
        ])

        serializer = MemberSerializer(member)
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def receive_gift(self, request, pk=None):
        """Отмечает, что участник получил подарок."""
        member = self.get_member(request, pk)

        if member.season.is_closed():
            raise ValidationError('Сезон перенесен в архив.')

        if not member.santa:
            raise ValidationError('У вас нет АДМ.')

        if member.is_gift_received():
            raise ValidationError('Подарок уже получен.')
        member.gift_received = timezone.now()
        member.santa.send_notification(
            'Ваш подарок получен',
            'Ваш АПП отметил в профиле, что подарок получен.')
        member.save()

        cache.delete_many([
            'member_%d_%s' % (member.user.id, pk),
            'member_%d_%s' % (member.santa.user.id, pk),
        ])

        serializer = MemberSerializer(member)
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def signup(self, request, pk=None):
        """Регистрирует участника на сезон."""
        season = self.get_season(pk)
        if not season.is_participatable():
            raise ValidationError('Регистрация на сезон завершена.')

        try:
            self.get_member(request, pk)
            raise ValidationError('Вы уже зарегистрированы на этот сезон.')
        except Http404:
            if not request.user.profile.can_participate():
                logger.warning('%s идет против системы.', request.user.username)
                raise ValidationError('Вы не можете участвовать в Клубе АДМ.')

        serializer = MemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(season=season, user=request.user)

        # Чтобы сбросить счетчик участников.
        self.delete_season_cache(pk)

        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def signout(self, request, pk=None):
        """Отменить участие."""
        member = self.get_member(request, pk)

        if member.giftee or not member.season.is_participatable():
            raise ValidationError('Слишком поздно.')

        member.delete()
        self.delete_member_cache(request, pk)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_season_key(self, year):
        return 'season_%s' % year

    def get_season(self, year):
        season_key = self.get_season_key(year)
        season = cache.get(season_key)

        if not season:
            try:
                season = season = Season.objects.get_by_year(year)
            except (Season.DoesNotExist, ValueError):
                raise Http404
            cache.set(season_key, season)

        return season

    def delete_season_cache(self, year):
        season_key = self.get_season_key(year)
        cache.delete(season_key)

    def get_member_key(self, user_id, year):
        return 'member_%d_%s' % (user_id, year)

    def get_member(self, request, year):
        member_key = self.get_member_key(request.user.id, year)
        member = cache.get(member_key)

        if not member:
            member = Member.objects.get_by_user_and_year(request.user.id, year)
            cache.set(member_key, member)

        return member

    def delete_member_cache(self, request, year):
        member_key = self.get_member_key(request.user.id, year)
        cache.delete(member_key)

    def get_mails_key(self, member_id):
        return 'mails_%d' % member_id

    def get_mails(self, member):
        mails_key = self.get_mails_key(member.id)
        mails = cache.get(mails_key)

        if not mails:
            santa_mails = list(Mail.objects.filter(
                Q(sender=member, recipient=member.santa) |
                Q(sender=member.santa, recipient=member)
            ))
            giftee_mails = list(Mail.objects.filter(
                Q(sender=member, recipient=member.giftee) |
                Q(sender=member.giftee, recipient=member)
            ))
            mails = {
                'santa': santa_mails,
                'giftee': giftee_mails
            }
            cache.set(mails_key, mails)

        return mails

    def delete_mails_cache(self, member):
        mails_key = self.get_mails_key(member.id)
        cache.delete(mails_key)


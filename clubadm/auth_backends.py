import logging
import requests

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.cache import cache

from clubadm.models import Profile


logger = logging.getLogger(__name__)


class TMServiceBackend(ModelBackend):
    def authenticate(self, access_token=None):
        service_profile = self.get_service_profile(access_token)
        profile_id = service_profile.get('id')

        try:
            profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            username = service_profile.get('login')

            try:
                user = User.objects.get(username__iexact=username)
                logger.debug('Пользователь %s существует, связываю его с '
                             'новым профилем %d.', username, profile_id)
            except User.DoesNotExist:
                user = User(username=username)
                user.save()

            profile = Profile(id=profile_id)
            profile.user = user

        if profile.access_token != access_token:
            logger.debug('Токен доступа изменился: %s -> %s.',
                         profile.access_token, access_token)
            profile.access_token = access_token
            profile.save()

        return profile.user

    def get_service_profile(self, access_token):
        if not access_token:
            return None

        service_profile_key = 'service_profile_%s' % access_token
        service_profile = cache.get(service_profile_key)

        if not service_profile:
            logger.debug('Кеш для %s не найден, делаю запрос.', access_token)
            url = '%s%s' % (settings.TMAUTH_ENDPOINT_URL, '/users/me')
            response = requests.get(url, headers = {
                'client': settings.TMAUTH_CLIENT,
                'token': access_token
            })
            response.raise_for_status()
            service_profile = response.json().get('data')
            cache.set(service_profile_key, service_profile)
            logger.debug(service_profile)

        return service_profile

    def get_user(self, user_id):
        user_key = 'user_%d' % user_id
        user = cache.get(user_key)

        if not user:
            try:
                user = User.objects.select_related('profile').get(id=user_id)
                cache.set(user_key, user)
            except User.DoesNotExist:
                return None

        return user

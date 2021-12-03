import requests
import secrets

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache

from clubadm.models import User


class TechMediaBackend(ModelBackend):
    def authenticate(self, access_token=None):
        remote = self.get_remote_user(access_token)
        if not remote:
            return None
        user_id = remote.get("id")
        username = remote.get("login")
        changed = False
        try:
            user = User.objects.get_by_id(user_id)
        except User.DoesNotExist:
            user = User(pk=user_id, username=username)
            user.email_token = secrets.token_urlsafe(24)
            changed = True
        if user.username != username:
            user.username = username
            changed = True
        if user.access_token != access_token:
            user.access_token = access_token
            changed = True
        if changed:
            user.save()
        return user

    def get_remote_user(self, access_token):
        if not access_token:
            return None
        user_key = "token:%s" % access_token
        user = cache.get(user_key)
        if not user:
            url = "%s/users/me" % settings.TMAUTH_ENDPOINT_URL
            response = requests.get(url, headers={
                "client": settings.TMAUTH_CLIENT,
                "token": access_token
            })
            if response.status_code != 200:
                return False
            user = response.json().get("data")
            cache.set(user_key, user)
        return user

    def get_user(self, user_id):
        try:
            user = User.objects.get_by_id(user_id)
        except:
            return None
        if not user.remote:
            return None
        return user

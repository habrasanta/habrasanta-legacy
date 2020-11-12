from django.http import Http404
from django.utils import timezone

from clubadm.models import Member, Season


class SeasonMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if "year" in view_kwargs:
            year = int(view_kwargs["year"])
            try:
                request.season = Season.objects.get_by_year(year)
            except Season.DoesNotExist:
                raise Http404("Такой сезон еще не создан")


class MemberMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if "year" in view_kwargs and request.user.is_authenticated:
            year = int(view_kwargs["year"])
            try:
                request.member = Member.objects.get_by_user_and_year(
                    request.user, year)
            except Member.DoesNotExist:
                request.member = None


class XUserMiddleware(object):
    def process_response(self, request, response):
        if not hasattr(request, "user"):
            return response
        if request.user.is_anonymous:
            return response
        # Чтобы Nginx мог писать имя пользователя в логи
        response["X-User"] = request.user.username
        return response

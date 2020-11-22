import json
import logging
import requests

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import urlencode

from clubadm.models import Season, Member, Mail
from clubadm.serializers import SeasonSerializer, MemberSerializer, UserSerializer


logger = logging.getLogger(__name__)


class _AjaxException(Exception):
    pass


class _AjaxResponse(HttpResponse):
    def __init__(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False, separators=(",", ": "), indent=2)
        super(_AjaxResponse, self).__init__(
            content=content, status=status, charset="utf-8",
            content_type="application/json;charset=utf-8")


def _ajax_view(member_required=False, match_required=False):
    def decorator(func):
        def view(request, *args, **kwargs):
            if request.method != "POST":
                return _AjaxResponse({
                    "error": "Используйте POST, пожалуйста"
                }, status=405)
            if request.user.is_anonymous:
                return _AjaxResponse({
                    "error": "Представьтесь, пожалуйста"
                }, status=403)
            if member_required and not request.member:
                return _AjaxResponse({
                    "error": "Ой, а вы во всем этом и не участвуете"
                }, status=403)
            if match_required and not request.member.giftee_id:
                return _AjaxResponse({
                    "error": "Давайте дождемся жеребьевки, а там посмотрим"
                }, status=403)
            try:
                return func(request)
            except _AjaxException as e:
                return _AjaxResponse({
                    "error": str(e)
                }, status=400)
        return view
    return decorator


def _create_login_url(request, next):
    redirect_uri = "{callback}?{params}".format(
        callback=reverse("callback"),
        params=urlencode({ "next": next })
    )
    return "{login_url}?{params}".format(
        login_url=settings.TMAUTH_LOGIN_URL,
        params=urlencode({
            "client_id": settings.TMAUTH_CLIENT,
            "response_type": "code",
            "redirect_uri": request.build_absolute_uri(redirect_uri),
        })
    )


def home(request):
    try:
        season = Season.objects.latest()
    except Season.DoesNotExist:
        return redirect("admin:clubadm_season_add")
    if request.user.is_authenticated:
        return redirect("profile", year=season.year)
    return redirect("welcome", year=season.year)


def welcome(request, year):
    if request.user.is_authenticated:
        return redirect("profile", year=year)
    login_url = _create_login_url(request, '/{}/profile/'.format(year))
    return render(request, "clubadm/welcome.html", {
        "season": request.season,
        "login_url": login_url,
    })


def profile(request, year):
    if request.user.is_anonymous:
        return redirect("welcome", year=year)

    prefetched = {
        "season": SeasonSerializer(request.season).data,
        "user": UserSerializer(request.user).data,
        "member": None,
    }

    if request.member:
        prefetched["member"] = MemberSerializer(request.member).data

    return render(request, "clubadm/profile.html", {
        "season": request.season,
        "prefetched": json.dumps(prefetched, ensure_ascii=False),
    })


def profile_legacy(request):
    if "hash" in request.GET:
        return redirect("profile", year=2012)
    return redirect("profile", year=2013)


def login(request):
    next = request.GET.get("next", reverse("home"))
    return HttpResponseRedirect(_create_login_url(request, next))


def callback(request):
    redirect_to = request.GET.get("next", reverse("home"))

    if request.user.is_authenticated:
        return HttpResponseRedirect(redirect_to)

    if "error" in request.GET:
        return redirect("home")

    response = requests.post(settings.TMAUTH_TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": request.GET.get("code"),
        "client_id": settings.TMAUTH_CLIENT,
        "client_secret": settings.TMAUTH_SECRET
    })

    if response.status_code != 200:
        logger.warning(response.text)
        return HttpResponse("Хабр вернул ошибку. Попробуйте снова.",
                            content_type="text/plain;charset=utf-8")

    user = authenticate(access_token=response.json().get("access_token"))
    auth_login(request, user)

    return HttpResponseRedirect(redirect_to)


@_ajax_view(member_required=False, match_required=False)
def signup(request):
    if not request.season.is_participatable:
        raise _AjaxException("Регистрация на этот сезон не возможна")
    if request.member:
        raise _AjaxException("Вы уже зарегистрированы на этот сезон")
    if not request.user.can_participate:
        raise _AjaxException("Вы не можете участвовать в нашем клубе")
    serializer = MemberSerializer(data=request.POST)
    if not serializer.is_valid():
        raise _AjaxException("Форма заполнена неверно")
    serializer.save(season=request.season, user=request.user)
    cache.delete(request.season.cache_key)
    request.season.members += 1
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": serializer.data,
    })


@_ajax_view(member_required=True, match_required=False)
def signout(request):
    if not request.season.is_participatable or request.member.giftee_id:
        raise _AjaxException("Время на решение истекло")
    request.member.delete()
    cache.delete(request.season.cache_key)
    request.season.members -= 1
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": None,
    })


@_ajax_view(member_required=True, match_required=True)
def send_mail(request):
    if request.season.is_closed:
        raise _AjaxException("Этот сезон находится в архиве")
    body = request.POST.get("body", "")
    if not body.strip():
        raise _AjaxException("Вначале нужно что-то написать")
    recipient = request.POST.get("recipient", "")
    if recipient == "giftee":
        request.member.send_mail(body, request.member.giftee)
        request.member.giftee.user.send_notification(
            "Новое сообщение от Деда Мороза",
            "clubadm/notifications/santa_mail.html", {
                "season": request.season
            }
        )
    elif recipient == "santa":
        request.member.send_mail(body, request.member.santa)
        request.member.santa.user.send_notification(
            "Новое сообщение от получателя подарка",
            "clubadm/notifications/giftee_mail.html", {
                "season": request.season
            }
        )
    else:
        raise _AjaxException("Неизвестный получатель")
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": MemberSerializer(request.member).data,
    })


@_ajax_view(member_required=True, match_required=True)
def read_mails(request):
    sender = request.POST.get("sender", "")
    timestamp = request.POST.get("timestamp", 0.0)
    try:
        timestamp = float(timestamp)
    except ValueError:
        raise _AjaxException("Нахрена тут строка?")
    if sender == "giftee":
        request.member.read_mails(request.member.giftee, timestamp)
    elif sender == "santa":
        request.member.read_mails(request.member.santa, timestamp)
    else:
        raise _AjaxException("Неизвестный отправитель")
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": MemberSerializer(request.member).data,
    })


@_ajax_view(member_required=True, match_required=True)
def send_gift(request):
    if request.season.is_closed:
        raise _AjaxException("Этот сезон находится в архиве")
    if request.member.is_gift_sent:
        raise _AjaxException("Вами уже был отправлен один подарок")
    request.member.send_gift()
    cache.delete(request.season.cache_key)
    request.season.sent += 1
    request.member.giftee.user.send_notification(
        "Вам отправлен подарок", "clubadm/notifications/gift_sent.html")
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": MemberSerializer(request.member).data,
    })


@_ajax_view(member_required=True, match_required=True)
def receive_gift(request):
    if request.season.is_closed:
        raise _AjaxException("Этот сезон находится в архиве")
    if request.member.is_gift_received:
        raise _AjaxException("Вами уже был получен один подарок")
    request.member.receive_gift()
    cache.delete(request.season.cache_key)
    request.season.received += 1
    request.member.santa.user.send_notification(
        "Ваш подарок получен", "clubadm/notifications/gift_received.html")
    return _AjaxResponse({
        "season": SeasonSerializer(request.season).data,
        "member": MemberSerializer(request.member).data,
    })

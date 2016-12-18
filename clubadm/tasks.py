import logging
import requests

from django.conf import settings

from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task
def match_members(year):
    from clubadm.models import Member
    # TODO(kafeman): Придумать что-нибудь сложнее и интереснее.
    members = Member.objects.filter(season_id=year).order_by("?")
    last = len(members) - 1
    for i, member in enumerate(members):
        if i == last:
            giftee = members[0]
        else:
            giftee = members[i + 1]
        member.giftee = giftee
        member.save()
        logger.debug("%s отправляет подарок %s", member, giftee)
        try:
            member.user.send_notification(
                "Пора отправлять подарок!",
                "clubadm/notifications/match.html", {
                    "year": year
                })
        except:
            logger.warning("Не удалось отправить уведомление %s", member)


@shared_task
def send_notification(access_token, title, text):
    url = "%s/tracker" % settings.TMAUTH_ENDPOINT_URL
    headers = {
        "client": settings.TMAUTH_CLIENT,
        "token": access_token
    }
    data = {
        "title": title,
        "text": text
    }
    response = requests.put(url, headers=headers, data=data)
    response.raise_for_status()

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from actionlog.models import LogEntry
from clubadm.signals import member_enrolled, member_unenrolled, user_banned, user_unbanned, giftee_mailed, santa_mailed, gift_sent, gift_received


@receiver(user_logged_in, dispatch_uid="actionlog.log_user_login")
def log_user_login(sender, user, request, **kwargs):
    entry = LogEntry(type=LogEntry.LOGGED_IN, user=user,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(user_logged_out, dispatch_uid="actionlog.log_user_logout")
def log_user_logout(sender, user, request, **kwargs):
    entry = LogEntry(type=LogEntry.LOGGED_OUT, user=user,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(member_enrolled, dispatch_uid="actionlog.log_member_enrollment")
def log_member_enrollment(sender, member, request, **kwargs):
    entry = LogEntry(type=LogEntry.ENROLLED,
                     user=member.user, target_season=member.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(member_unenrolled, dispatch_uid="actionlog.log_member_unenrollmenet")
def log_member_unenrollment(sender, request, **kwargs):
    entry = LogEntry(type=LogEntry.UNENROLLED,
                     user=request.user, target_season=request.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(user_banned, dispatch_uid="actionlog.log_user_ban")
def log_user_ban(sender, user, request, **kwargs):
    entry = LogEntry(type=LogEntry.BANNED,
                     user=request.user, target_user=user,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(user_unbanned, dispatch_uid="actionlog.log_user_unban")
def log_user_unban(sender, user, request, **kwargs):
    entry = LogEntry(type=LogEntry.UNBANNED,
                     user=request.user, target_user=user,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(santa_mailed, dispatch_uid="actionlog.log_santa_mail")
def log_santa_mail(sender, request, **kwargs):
    entry = LogEntry(type=LogEntry.PM_SANTA,
                     user=request.user, target_season=request.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(giftee_mailed, dispatch_uid="actionlog.log_giftee_mail")
def log_giftee_mail(sender, request, **kwargs):
    entry = LogEntry(type=LogEntry.PM_GIFTEE,
                     user=request.user, target_season=request.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(gift_received, dispatch_uid="actionlog.log_gift_reception")
def log_gift_reception(sender, request, **kwargs):
    entry = LogEntry(type=LogEntry.GIFT_RECEIVED,
                     user=request.user, target_season=request.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()


@receiver(gift_sent, dispatch_uid="actionlog.log_gift_shipment")
def log_gift_shipment(sender, request, **kwargs):
    entry = LogEntry(type=LogEntry.GIFT_SENT,
                     user=request.user, target_season=request.season,
                     ip_address=request.META["REMOTE_ADDR"])
    entry.save()

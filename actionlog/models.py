from django.db import models
from django.utils import timezone

from clubadm.models import User, Season


class LogEntry(models.Model):
    LOGGED_IN = 1
    LOGGED_OUT = 2
    ENROLLED = 3
    UNENROLLED = 4
    GIFT_SENT = 5
    GIFT_RECEIVED = 6
    PM_SANTA = 7
    PM_GIFTEE = 8
    BANNED = 9
    UNBANNED = 10

    type = models.IntegerField() # action; shortint
    user = models.ForeignKey(User, related_name="actions") # actor
    target_user = models.ForeignKey(User, null=True, related_name="actions2")
    target_season = models.ForeignKey(Season, null=True)
    date = models.DateTimeField(default=timezone.now)
    ip_address = models.CharField(max_length=45)

    class Meta:
        db_table = "audit_log"

from django.dispatch import Signal


member_enrolled = Signal()
member_unenrolled = Signal()

user_banned = Signal()
user_unbanned = Signal()

giftee_mailed = Signal()
santa_mailed = Signal()

gift_sent = Signal()
gift_received = Signal()

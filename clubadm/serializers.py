from datetime import date

from rest_framework import serializers

from clubadm.models import Member, Season, Mail, User


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    can_participate = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("username", "avatar", "is_active", "can_participate")

    def get_avatar(self, obj):
        return obj.avatar

    def get_is_active(self, obj):
        return not obj.is_banned

    def get_can_participate(self, obj):
        return obj.can_participate


class SeasonSerializer(serializers.HyperlinkedModelSerializer):
    members = serializers.SerializerMethodField()
    sent = serializers.SerializerMethodField()
    received = serializers.SerializerMethodField()
    timeleft = serializers.SerializerMethodField()
    is_closed = serializers.SerializerMethodField()
    is_participatable = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ("year", "signups_start", "signups_end", "ship_by", "members",
                  "sent", "received", "timeleft", "is_closed",
                  "is_participatable", "gallery")

    def get_members(self, obj):
        return obj.members

    def get_sent(self, obj):
        return obj.sent

    def get_received(self, obj):
        return obj.received

    def get_timeleft(self, obj):
        timeleft = (obj.signups_end - date.today()).days
        if timeleft > 0:
            return timeleft
        return None

    def get_is_closed(self, obj):
        return obj.is_closed

    def get_is_participatable(self, obj):
        return obj.is_participatable

    def get_gallery(self, obj):
        if obj.gallery:
            return obj.gallery
        return None


class GifteeSerializer(serializers.ModelSerializer):
    unread = serializers.SerializerMethodField()
    mails = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ("fullname", "postcode", "address", "unread", "mails",
                  "is_gift_received")

    def get_unread(self, obj):
        import datetime
        from django.utils import timezone
        return Mail.objects.filter(
            sender=obj,
            recipient=obj.santa,
            read_date__isnull=True,
            send_date__gte=timezone.make_aware(datetime.datetime(2016, 12, 20))
        ).count()

    def get_mails(self, obj):
        mails = Mail.objects.get_between(obj, obj.santa)
        return MailSerializer(mails, context={
            "author_id": obj.santa.id
        }, many=True).data


class SantaSerializer(serializers.ModelSerializer):
    unread = serializers.SerializerMethodField()
    mails = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ("unread", "mails", "is_gift_sent")

    def get_unread(self, obj):
        import datetime
        from django.utils import timezone
        return Mail.objects.filter(
            sender=obj,
            recipient=obj.giftee,
            read_date__isnull=True,
            send_date__gte=timezone.make_aware(datetime.datetime(2016, 12, 20))
        ).count()

    def get_mails(self, obj):
        mails = Mail.objects.get_between(obj, obj.giftee)
        return MailSerializer(mails, context={
            "author_id": obj.giftee_id
        }, many=True).data


class MemberSerializer(serializers.ModelSerializer):
    giftee = GifteeSerializer(read_only=True)
    santa = SantaSerializer(read_only=True)

    class Meta:
        model = Member
        fields = ("fullname", "postcode", "address", "giftee", "santa",
                  "is_gift_sent", "is_gift_received")
        read_only_fields = ("is_gift_sent", "is_gift_received")

    def validate_fullname(self, value):
        if " " not in value.strip():
            # Надоели придурки, которые в поле "Полное имя" пишут "Вася".
            raise serializers.ValidationError("Вы должны ввести полное имя")
        return value


class MailSerializer(serializers.ModelSerializer):
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Mail
        fields = ("is_author", "body", "send_date", "read_date")

    def get_is_author(self, obj):
        return obj.sender_id == self.context["author_id"]

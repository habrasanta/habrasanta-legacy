from datetime import date

from django.contrib.auth.models import User
from django.core.cache import cache

from rest_framework import serializers

from clubadm.models import Member, Profile, Season, Mail


class SeasonSerializer(serializers.HyperlinkedModelSerializer):
    members = serializers.SerializerMethodField()
    sent = serializers.SerializerMethodField()
    received = serializers.SerializerMethodField()
    timeleft = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ('year', 'signups_start', 'signups_end', 'ship_by', 'members',
                  'sent', 'received', 'timeleft', 'is_closed',
                  'is_participatable', 'gallery')

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


class GifteeSerializer(serializers.ModelSerializer):
    is_female = serializers.SerializerMethodField()
    chat_name = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ('fullname', 'postcode', 'address', 'is_female', 'chat_name',
                  'is_gift_received', 'last_visit')

    def get_is_female(self, obj):
        return obj.user.profile.is_female()

    def get_chat_name(self, obj):
        profile = obj.user.profile
        if profile.is_male():
            return 'Внучек'
        if profile.is_female():
            return 'Внучка'
        return 'АПП' # Пользователь предпочел не раскрывать свой пол.


class SantaSerializer(serializers.ModelSerializer):
    is_female = serializers.SerializerMethodField()
    chat_name = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ('is_female', 'chat_name', 'is_gift_sent', 'last_visit')

    def get_is_female(self, obj):
        return obj.user.profile.is_female()

    def get_chat_name(self, obj):
        profile = obj.user.profile
        if profile.is_male():
            return 'Дед Мороз'
        if profile.is_female():
            return 'Снегурочка'
        return 'АДМ' # Пользователь предпочел не раскрывать свой пол.


class MemberSerializer(serializers.ModelSerializer):
    giftee = GifteeSerializer(read_only=True)
    santa = SantaSerializer(read_only=True)

    class Meta:
        model = Member
        fields = ('fullname', 'postcode', 'address', 'giftee', 'santa',
                  'is_gift_sent', 'is_gift_received')
        read_only_fields = ('is_gift_sent', 'is_gift_received')


class MailSerializer(serializers.ModelSerializer):
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Mail
        fields = ('is_author', 'body', 'sent')

    def get_is_author(self, obj):
        return obj.sender == self.context.get('member')


class ChatSerializer(serializers.Serializer):
    santa = MailSerializer(many=True)
    giftee = MailSerializer(many=True)

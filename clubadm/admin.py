from django.contrib import admin
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.views.decorators.cache import never_cache

from clubadm.forms import SeasonForm
from clubadm.models import Member, Season, User
from clubadm.tasks import match_members


class SeasonAdmin(admin.ModelAdmin):
    actions = ("match_members", "give_badges", "block_members", "clear_cache")
    fieldsets = (
        (None, {
            "fields": ("year",)
        }),
        ("Сроки проведения", {
            "fields": ("signups_start", "signups_end", "ship_by")
        }),
        ("Прочее", {
            "fields": ("gallery",)
        })
    )
    form = SeasonForm
    list_display = ("year", "signups_start", "signups_end", "ship_by",
                    "is_closed", "is_participatable")
    ordering = ("year",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("year",)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.is_participatable is True

    def is_closed(self, obj):
        return obj.is_closed
    is_closed.boolean = True
    is_closed.short_description = "сезон завершен"

    def is_participatable(self, obj):
        return obj.is_participatable
    is_participatable.boolean = True
    is_participatable.short_description = "регистрация открыта"

    def match_members(self, request, queryset):
        for obj in queryset:
            match_members.delay(obj.year)
        self.message_user(request, "Процесс сортировки был запущен")
    match_members.short_description = "Провести жеребьевку"

    def give_badges(self, request, queryset):
        array = []
        for obj in queryset:
            members = obj.member_set.filter(
                gift_sent__isnull=False,
                giftee__gift_received__isnull=False)
            for member in members:
                array.append([
                    member.user.username,
                    member.user_id
                ])
        return JsonResponse(array, safe=False)
    give_badges.short_description = "Раздать значки \"Дед Мороз\""

    def block_members(self, request, queryset):
        self.message_user(request, "TODO")
    block_members.short_description = "Заблокировать плохишей"

    def clear_cache(self, request, queryset):
        for obj in queryset:
            cache.delete(obj.cache_key)
        cache.delete("season:latest")
        self.message_user(request, "Кеш успешно очищен")
    clear_cache.short_description = "Очистить кеш"


class MemberInline(admin.StackedInline):
    can_delete = False
    fieldsets = (
        (None, {
            "fields": ("fullname", "postcode", "address", "is_gift_sent",
                       "is_gift_received")
        }),
    )
    max_num = 0
    model = Member
    readonly_fields = ("fullname", "postcode", "address", "is_gift_sent",
                       "is_gift_received")
    show_change_link = True
    verbose_name_plural = "история участия"

    def is_gift_sent(self, obj):
        return obj.is_gift_sent
    is_gift_sent.boolean = True
    is_gift_sent.short_description = "подарок отправлен"

    def is_gift_received(self, obj):
        return obj.is_gift_received
    is_gift_received.boolean = True
    is_gift_received.short_description = "подарок получен"


class UserAdmin(admin.ModelAdmin):
    actions = ("ban",)
    fieldsets = (
        (None, {
            "fields": ("username",)
        }),
        ("Аккаунт", {
            "fields": ("get_avatar", "get_karma", "get_rating", "get_rights")
        }),
        ("Права", {
            "fields": ("is_oldfag", "is_banned")
        }),
        ("Важные даты", {
            "fields": ("first_login", "last_login")
        }),
    )
    search_fields = ("username",)
    list_display = ("username", "first_login", "last_login")
    readonly_fields = ("username", "get_avatar", "get_karma", "get_rating",
                       "get_rights", "first_login", "last_login")
    inlines = (MemberInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def construct_change_message(self, request, form, formsets, add=False):
        if add:
            return super(UserAdmin, self).construct_change_message(
                request, form, formsets, add)
        if "is_banned" in form.changed_data:
            was_banned = form.initial["is_banned"]
            is_banned = form.cleaned_data["is_banned"]
            if was_banned and not is_banned:
                return "Пользователь разбанен."
            if not was_banned and is_banned:
                return "Пользователь забанен."
        if "is_oldfag" in form.changed_data:
            was_oldfag = form.initial["is_oldfag"]
            is_oldfag = form.cleaned_data["is_oldfag"]
            if was_oldfag and not is_oldfag:
                return "Для пользователя введено ограничение по карме."
            if not was_oldfag and is_oldfag:
                return "Для пользователя снято ограничение по карме."
        return super(UserAdmin, self).construct_change_message(
            request, form, formsets, add)

    def view_on_site(self, obj):
        return "https://habrahabr.ru/users/%s/" % obj.username

    def ban(self, request, queryset):
        queryset.update(is_banned=True)
    ban.short_description = "Забанить выбранных пользователей"

    def get_karma(self, obj):
        if obj.karma > 0: color = "#6c9007"
        elif obj.karma < 0: color = "#d53c30"
        else: color = "#c6d4d8"
        template = "<span style=\"font-weight:bold;color:{}\">{}</span>"
        return format_html(template, color, obj.karma)
    get_karma.short_description = "карма"

    def get_avatar(self, obj):
        template = "<img src=\"{}\" style=\"{}\">"
        style = "width:32px;height:32px;border-radius:5px"
        return format_html(template, obj.avatar, style)
    get_avatar.short_description = "аватар"

    def get_rating(self, obj):
        template = "<span style=\"font-weight:bold;color:#c6c\">{}</span>"
        return format_html(template, obj.rating)
    get_rating.short_description = "рейтинг"

    def get_rights(self, obj):
        if obj.is_readonly:
            return "ReadOnly"
        if obj.is_readcomment:
            return "Read&Comment"
        return "Полноценный аккаунт"
    get_rights.short_description = "тип аккаунта"


class MemberAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            "fields": ("user", "season", "giftee_link", "santa_link")
        }),
        ("Почтовый адрес", {
            "fields": ("fullname", "postcode", "address")
        }),
        ("Важные даты", {
            "fields": ("gift_sent", "gift_received")
        }),
    )
    list_display = ("fullname", "season", "is_gift_sent", "is_gift_received")
    list_filter = ("season",)
    readonly_fields = ("giftee_link", "santa_link")
    search_fields = ("fullname",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user", "season")
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.giftee is None

    def is_gift_sent(self, obj):
        return obj.is_gift_sent
    is_gift_sent.boolean = True
    is_gift_sent.short_description = "подарок отправлен"

    def is_gift_received(self, obj):
        return obj.is_gift_received
    is_gift_received.boolean = True
    is_gift_received.short_description = "подарок получен"

    def giftee_link(self, obj):
        template = "<a href=\"{}\">{}</a> (<a href=\"{}\">{}</a>)"
        member_url = reverse("admin:clubadm_member_change", args=[obj.giftee_id])
        user_url = reverse("admin:clubadm_user_change", args=[obj.giftee.user_id]),
        return format_html(template, member_url, obj.giftee.fullname,
                           user_url, obj.giftee.user.username)
    giftee_link.short_description = "АПП"

    def santa_link(self, obj):
        template = "<a href=\"{}\">{}</a> (<a href=\"{}\">{}</a>)"
        member_url = reverse("admin:clubadm_member_change", args=[obj.santa.id])
        user_url = reverse("admin:clubadm_user_change", args=[obj.santa.user_id])
        return format_html(template, member_url, obj.santa.fullname,
                            user_url, obj.santa.user.username)
    santa_link.short_description = "АДМ"


class AdminSite(admin.AdminSite):
    site_header = "Кабинет Деда Мороза"
    site_title = "Клуб анонимных Дедов Морозов"

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_admin

    @never_cache
    def login(self, request, extra_context=None):
        index_path = reverse("admin:index", current_app=self.name)
        if request.user.is_authenticated:
            if request.user.is_admin:
                return HttpResponseRedirect(index_path)
            raise Http404("Админки не существует")
        query_string = urlencode({
            "next": request.GET.get("next", index_path)
        })
        return HttpResponseRedirect(
            "%s?%s" % (reverse("login"), query_string))


site = AdminSite()
site.register(Season, SeasonAdmin)
site.register(Member, MemberAdmin)
site.register(User, UserAdmin)

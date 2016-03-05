from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.core.cache import cache

from clubadm.forms import SeasonForm, UserForm
from clubadm.models import Member, Profile, Season
from clubadm.tasks import match_members


class SeasonAdmin(admin.ModelAdmin):
    actions = ('match_members', 'block_members', 'clear_cache')
    fieldsets = (
        (None, {'fields': ('year',)}),
        ('Сроки проведения', {
            'fields': ('signups_start', 'signups_end', 'ship_by')
        }),
        ('Прочее', {'fields': ('gallery',)})
    )
    form = SeasonForm
    list_display = ('year', 'signups_start', 'signups_end', 'ship_by',
                    'is_closed', 'is_participatable')
    ordering = ('year',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('year',)
        return self.readonly_fields

    # TODO(kafeman): Автоматически создавать задачу сортировки при сохранении.
    def match_members(self, request, queryset):
        for obj in queryset:
            match_members.delay(obj.year)
        self.message_user(request, 'Процесс сортировки был запущен.')
    match_members.short_description = 'Провести жеребьевку'

    # TODO(kafeman): Автоматически создавать задачу бана при сохранении.
    def block_members(self, request, queryset):
        for obj in queryset:
            pass # TODO
    block_members.short_description = 'Заблокировать плохишей'

    def clear_cache(self, request, queryset):
        for obj in queryset:
            cache.delete('season_%d' % obj.year)
        cache.delete('season_latest')
        self.message_user(request, 'Кеш успешно очищен.')
    clear_cache.short_description = 'Очистить кеш'


class MemberInline(admin.StackedInline):
    can_delete = False
    fieldsets = (
        (None, {
            'fields': ('fullname', 'postcode', 'address', 'is_gift_sent',
                       'is_gift_received')
        }),
    )
    max_num = 0
    model = Member
    readonly_fields = ('giftee', 'fullname', 'postcode', 'address',
                       'is_gift_sent', 'is_gift_received')
    show_change_link = True
    verbose_name_plural = 'история участия'


class ProfileInline(admin.TabularInline):
    can_delete = False
    fieldsets = (
        (None, {
            'fields': ('karma', 'rating', 'is_readonly', 'can_participate',
                       'is_oldfag', 'access_token')
        }),
    )
    model = Profile
    readonly_fields = ('karma', 'rating', 'is_readonly', 'can_participate')
    verbose_name_plural = 'профиль'


class UserAdmin(UserAdmin):
    form = UserForm
    inlines = (MemberInline, ProfileInline)

    def has_add_permission(self, request):
        return False


class MemberAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user', 'season', 'giftee_link', 'santa_link')}),
        ('Почтовый адрес', {
            'fields': ('fullname', 'postcode', 'address')
        }),
        ('Важные даты', {
            'fields': ('last_visit', 'gift_sent', 'gift_received')
        }),
    )
    list_display = ('fullname', 'season', 'is_gift_sent', 'is_gift_received')
    list_filter = ('season',)
    readonly_fields = ('giftee_link', 'santa_link')
    search_fields = ('fullname',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'season')
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.giftee is None

    def giftee_link(self, obj):
        return '<a href="%s">%s</a> (<a href="%s">%s</a>)' % (
            urlresolvers.reverse('admin:clubadm_member_change', args=[
                obj.giftee.id
            ]),
            obj.giftee.fullname,
            urlresolvers.reverse('admin:auth_user_change', args=[
                obj.giftee.user.id
            ]),
            obj.giftee.user.username
        )
    giftee_link.allow_tags=True
    giftee_link.short_description = 'АПП'

    def santa_link(self, obj):
        return '<a href="%s">%s</a> (<a href="%s">%s</a>)' % (
            urlresolvers.reverse('admin:clubadm_member_change', args=[
                obj.santa.id
            ]),
            obj.santa.fullname,
            urlresolvers.reverse('admin:auth_user_change', args=[
                obj.santa.user.id
            ]),
            obj.santa.user.username
        )
    santa_link.allow_tags=True
    santa_link.short_description = 'АДМ'


admin.site.site_title = 'Админка Клуба АДМ'
admin.site.site_header = 'Кабинет Деда Мороза'

admin.site.register(Season, SeasonAdmin)
admin.site.register(Member, MemberAdmin)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

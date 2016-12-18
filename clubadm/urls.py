from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth.views import logout

from clubadm import views, admin


urlpatterns = [
    url(r"^$", views.home, name="home"),
    url(r"^login$", views.login, name="login"),
    url(r"^callback$", views.callback, name="callback"),
    url(r"^(?P<year>[0-9]{4})/$", views.welcome, name="welcome"),
    url(r"^(?P<year>[0-9]{4})/signup/$", views.signup, name="signup"),
    url(r"^(?P<year>[0-9]{4})/signout/$", views.signout, name="signout"),
    url(r"^(?P<year>[0-9]{4})/profile/$", views.profile, name="profile"),
    url(r"^(?P<year>[0-9]{4})/send_mail/$", views.send_mail, name="send_mail"),
    url(r"^(?P<year>[0-9]{4})/send_gift/$", views.send_gift, name="send_gift"),
    url(r"^(?P<year>[0-9]{4})/receive_gift/$", views.receive_gift, name="receive_gift"),
    url(r"^(?P<year>[0-9]{4})/read_mails/$", views.read_mails, name="read_mails"),
    url(r"^logout$", logout, {"next_page": "/"}),
    url(r"^profile$", views.profile_legacy),
    url(r"^admin/", admin.site.urls),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ]

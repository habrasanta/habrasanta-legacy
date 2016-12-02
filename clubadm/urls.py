from django.conf.urls import include, url
from django.contrib.auth.views import logout

from rest_framework.routers import SimpleRouter

from clubadm import views, admin


router = SimpleRouter(trailing_slash=False)
router.register(r'seasons', views.SeasonViewSet, base_name='season')


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login$', views.login, name='login'),
    url(r'^callback$', views.callback, name='callback'),
    url(r'^logout$', logout, {'next_page': '/'}),
    url(r'^', include(router.urls)),

    # Для старых ссылок со внешних ресурсов
    url(r'^profile$', views.oldprofile), # АДМ-2012 и АДМ-2013
    url(r'^(?P<year>[0-9]+)/profile$', views.oldprofile), # АДМ-2014

    # Админка
    url(r'^admin/', admin.site.urls),
]

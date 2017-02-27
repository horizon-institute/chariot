from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import logout_then_login
from django.views import static

from deployments.views import DeploymentListView
from hubs.views import HubCreateView
from .views import login_view, create_admin_view, DeviceListView

admin.autodiscover()

urlpatterns = [
    url(r'^$', DeploymentListView.as_view(), name='home'),
    url(r'^accounts/create/$', create_admin_view, name='auth_create_admin'),
    url(r'^accounts/login/$', login_view, name='auth_login'),
    url(r'^accounts/logout/$', logout_then_login, name='auth_logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('hubs.urls', namespace='hubs')),
    url(r'^deployments/', include('deployments.urls', namespace='deployments')),
    url(r'^devices', DeviceListView.as_view(), name='devices'),
    url(r'^graphs/', include('graphs.urls', namespace='graphs')),
    url(r'^hub/create', HubCreateView.as_view(), name='create_hub'),
    url(r'^media/(?P<path>.*)$', static.serve, {'document_root': settings.MEDIA_ROOT}),
]

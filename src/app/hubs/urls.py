from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url(r'^deployments', DeploymentListView.as_view(), name='deployments'),
    url(r'^deployment/(?P<pk>\d+)', DeploymentView.as_view(), name='data'),
    url(r'^deployment/(?P<pk>\d+)/data', DataView.as_view(), name='data'),
    url(r'^hub/(?P<id>[\w:-]+)/ping', HubPingView.as_view(), name='ping'),
    url(r'^hub/(?P<id>[\w:-]+)/sensors', SensorListView.as_view(), name='sensors'),
    url(r'^hub/(?P<id>[\w:-]+)/token', get_token, name='token'),
    url(r'^reading', SensorReading.as_view(), name='reading'),
)

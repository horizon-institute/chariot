from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
	'',
	url(r'^deployments', DeploymentListView.as_view(), name='desployments'),
	url(r'^hub/(?P<mac_address>[\w:-]+)/ping', HubPingView.as_view(), name='ping'),
	url(r'^hub/(?P<mac_address>[\w:-]+)/sensors', SensorListView.as_view(), name='sensors'),
	url(r'^hub/(?P<mac_address>[\w:-]+)/token', get_token, name='token'),
	url(r'^reading', SensorReadingCreateView.as_view(), name='reading')
)

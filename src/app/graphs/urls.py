from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url(r'^(?P<pk>\d+)$', DeploymentGraphView.as_view(), name='deployment'),
    url(r'^(?P<pk>\d+)/devices$', get_devices, name='devices'),
    url(r'^(?P<pk>\d+)/data/(?P<sensor>[-\d]+)/(?P<channel_name>[-\w]+)$', get_data, name='data'),
    url(r'^(?P<pk>\d+)/data', get_all_data, name='data'),
)

from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url(r'^(?P<pk>\d+)$', DeploymentGraphView.as_view(), name='deployment'),
    url(r'^(?P<pk>\d+)/data', get_all_data, name='data'),
)

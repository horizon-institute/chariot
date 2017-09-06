from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^(?P<pk>\d+)$', DeploymentGraphView.as_view(), name='deployment'),
    url(r'^(?P<pk>\d+)/prediction', DeploymentPredictionView.as_view(), name='prediction'),
    url(r'^(?P<pk>\d+)/data', get_all_data, name='data'),
]

from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^create', DeploymentCreateView.as_view(), name='create'),
    url(r'^(?P<pk>\d+)$', DeploymentUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>\d+)/end$', DeploymentEndView.as_view(), name='end'),
    url(r'^(?P<pk>\d+)/start$', DeploymentStartView.as_view(), name='start'),
    url(r'^(?P<pk>\d+)/fragment$', DeploymentDetailView.as_view(), name='fragment'),
    url(r'^(?P<pk>\d+)/sensor/(?P<id>\d+)$', DeploymentSensorView.as_view(), name='sensor'),

    url(r'^annotation$', DeploymentAnnotationCreate.as_view(), name='annotation-create'),
    url(r'^annotation/(?P<pk>\d+)$', DeploymentAnnotationUpdate.as_view(),
        name='annotation-update'),
    url(r'^annotation/(?P<pk>\d+)/delete$', DeploymentAnnotationDelete.as_view(),
        name='annotation-delete'),
]

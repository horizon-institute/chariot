from django.contrib import admin

from .models import *

admin.site.register(Deployment)
admin.site.register(DeploymentAnnotation)
admin.site.register(DeploymentSensor)
admin.site.register(DeploymentDataCache)

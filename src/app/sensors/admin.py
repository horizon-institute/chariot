# encoding:UTF-8
from models import Channel, Sensor

from django.contrib import admin


class SensorAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Fields', {'fields': ['name', 'id', 'sensor_type', 'default', 'channels']}),
    ]
    list_display = ('name', 'id')
    search_fields = ('user__username',)
    ordering = ('name',)


admin.site.register(Sensor, SensorAdmin)
admin.site.register(Channel)

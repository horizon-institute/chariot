# encoding:UTF-8
from models import SensorReading, Channel, Sensor

from django.contrib import admin


class SensorAdmin(admin.ModelAdmin):
	fieldsets = [
		('Fields', {'fields': ['name', 'identifier', 'sensor_type', 'default', 'channels']}),
	]
	list_display = ('name', 'identifier')
	search_fields = ('user__username',)
	ordering = ('name',)


class SensorReadingAdmin(admin.ModelAdmin):
	fieldsets = [
		('Fields', {'fields': ['timestamp', 'sensor', 'value', 'channel']}),
	]
	list_display = ('timestamp', 'sensor', 'channel', 'value')
	search_fields = ('sensor__user__username', 'channel')


admin.site.register(Sensor, SensorAdmin)
admin.site.register(Channel)
admin.site.register(SensorReading, SensorReadingAdmin)

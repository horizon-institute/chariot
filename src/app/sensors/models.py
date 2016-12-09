# encoding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from chariot.utils import LOCALE_DATE_FMT


class ChannelManager(models.Manager):
	def get_by_natural_key(self, name):
		return self.get(name=name)


class Channel(models.Model):
	objects = ChannelManager()

	name = models.CharField(_('Identifier'), max_length=32)
	units = models.CharField(_('Units of Measurement'), max_length=10)
	friendly_name = models.CharField(_('Name'), max_length=256)
	hidden = models.BooleanField(_("Hidden"), default=False)

	def natural_key(self):
		return self.name

	def __unicode__(self):
		return self.friendly_name


class SensorManager(models.Manager):
	def get_by_natural_key(self, identifier):
		return self.get(idetifier=identifier)


class Sensor(models.Model):
	objects = SensorManager()

	name = models.CharField(_('Name'), max_length=200)
	identifier = models.CharField(_('Identifier'), max_length=30, unique=True, db_index=True)
	sensor_type = models.CharField(_('Sensor Type'), max_length=30)
	channels = models.ManyToManyField(Channel)
	default = models.BooleanField(_('Add to New Deployments'), default=False)

	def __unicode__(self):
		return u'%s (%s)' % (self.name, self.identifier)

	def natural_key(self):
		return self.identifier


class SensorReading(models.Model):
	timestamp = models.DateTimeField(db_index=True)
	sensor = models.ForeignKey(Sensor, db_index=True)
	channel = models.ForeignKey(Channel, db_index=True)
	value = models.FloatField(_('value'), default=0)

	class Meta:
		ordering = ['timestamp']

	def __unicode__(self):
		return str(self.value) + ' @ ' + self.timestamp.strftime(LOCALE_DATE_FMT)

	hidden_fields = ['sensor', 'channel', 'id']

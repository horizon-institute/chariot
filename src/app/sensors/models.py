# encoding:UTF-8
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Channel(models.Model):
    id = models.CharField(_('Identifier'), primary_key=True, max_length=32)
    units = models.CharField(_('Units of Measurement'), max_length=10)
    name = models.CharField(_('Name'), max_length=256)
    hidden = models.BooleanField(_("Hidden"), default=False)
    aggregation = models.CharField(_('Aggregation'), default="2m", max_length=10)

    def __str__(self):
        return u'%s Channel' % self.name


class Sensor(models.Model):
    id = models.CharField(_('Identifier'), max_length=30, primary_key=True)
    name = models.CharField(_('Name'), max_length=200)
    sensor_type = models.CharField(_('Sensor Type'), max_length=30)
    channels = models.ManyToManyField(Channel)
    cost_channel = models.ForeignKey(Channel, blank=True, null=True, related_name='+')
    default = models.BooleanField(_('Add to New Deployments'), default=False)

    class Meta:
        ordering = ['name']

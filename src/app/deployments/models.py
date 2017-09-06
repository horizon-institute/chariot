# encoding:UTF-8
import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from chariot.influx import select

from hubs.models import Hub
from sensors.models import Sensor
from chariot.influx import drop_from

BOILER_TYPES = (
    (1, _("Gas")),
    (2, _("Electric"))
)


class Deployment(models.Model):
    client_name = models.CharField(max_length=255)
    address_line_one = models.CharField(max_length=255)
    post_code = models.CharField(max_length=255)
    notes = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    photo = models.ImageField(_('Header Image'), null=True, blank=True,
                              upload_to='deployment_photos')

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    boiler_manufacturer = models.CharField(max_length=255, null=True, blank=True)
    boiler_model = models.CharField(max_length=255, null=True, blank=True)
    boiler_output = models.FloatField(null=True, blank=True)
    boiler_efficiency = models.FloatField(null=True, blank=True)
    boiler_type = models.IntegerField(choices=BOILER_TYPES, default=1)
    boiler_thermostat = models.FloatField(default=20)

    building_area = models.FloatField(default=0)
    building_height = models.FloatField(default=0)

    hub = models.OneToOneField(Hub, blank=True, null=True)

    prediction = models.TextField(null=True, blank=True)

    def __str__(self):
        return '{client} Deployment'.format(client=self.client_name)

    def end(self):
        if not self.running:
            raise ValueError('Deployment is not running')

        self.hub = None
        self.end_date = timezone.datetime.now()
        self.save()

    @property
    def running(self):
        return self.start_date is not None and self.end_date is None

    def start(self):
        if self.running:
            raise ValueError('Deployment is already running')

        for sensor in self.sensors.all():
            for channel in sensor.sensor.channels.all():
                drop_from(channel.name).where('deployment').eq(self.pk)

        self.start_date = timezone.datetime.now()
        self.save()

    @property
    def status(self):
        if self.end_date is not None:
            return 4, 'Deployment Ended'
        elif self.hub and self.sensors.exists():
            if self.running:
                return 3, 'Deployment Running'
            else:
                return 2, 'Deployment not running'

        return 1, 'Details Incomplete'


class DeploymentAnnotation(models.Model):
    text = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    layer = models.IntegerField()
    author = models.ForeignKey(User)
    deployment = models.ForeignKey(Deployment)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Deployment Annotations"


class DeploymentSensor(models.Model):
    deployment = models.ForeignKey(Deployment, related_name='sensors')
    sensor = models.ForeignKey(Sensor)
    room_area = models.FloatField(default=0)
    room_height = models.FloatField(default=2.4)
    nearest_thermostat = models.BooleanField(default=False)
    cost = models.FloatField(default=0)
    location = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['sensor']
        verbose_name_plural = "Deployment Sensors"
        unique_together = ("deployment", "sensor")

    def __str__(self):
        return 'Sensor {sensor} for {deployment}'.format(
            sensor=self.sensor.name, deployment=self.deployment
        )

    @property
    def has_data(self):
        channels = []
        for channel in self.sensor.channels.all():
            try:
                result = select('LAST').from_table(channel.id) \
                    .where('deployment').eq(self.deployment.pk) \
                    .where('sensor').eq(self.sensor.id).first()
                if result:
                    channels.append(channel)
            except Exception as e:
                pass

        return len(channels) > 0

    @property
    def latest_reading(self):
        latest_reading = {}

        for channel in self.sensor.channels.all():
            try:
                result = select('LAST').from_table(channel.id) \
                    .where('deployment').eq(self.deployment.pk) \
                    .where('sensor').eq(self.sensor.id).first()
                if result:
                    if not latest_reading or result['time'] > latest_reading['time']:
                        latest_reading = {
                            'channel': channel,
                            'result': result,
                            'time': datetime.datetime.fromtimestamp(result['time']/1000.0),
                            'value': result['last']
                        }
            except Exception as e:
                pass

        return latest_reading

    @property
    def latest_readings(self):
        latest_readings = []

        for channel in self.sensor.channels.all():
            try:
                result = select('LAST').from_table(channel.id) \
                    .where('deployment').eq(self.deployment.pk) \
                    .where('sensor').eq(self.sensor.id).first()
                latest_readings.append({
                    'channel': channel,
                    'result': result,
                    'time': result['time'],
                    'value': result['last']
                })
            except Exception as e:
                latest_readings.append({
                    'channel': channel,
                    'e': repr(e)
                })

        return latest_readings

    def save(self, *args, **kwargs):
        if not self.id:
            try:
                DeploymentSensor.objects.get(
                    deployment=self.deployment,
                    sensor=self.sensor
                )
                raise ValidationError('A SensorDeployment with that deployment and sensor combo already exists')
            except DeploymentSensor.DoesNotExist:
                pass

        super(DeploymentSensor, self).save(*args, **kwargs)

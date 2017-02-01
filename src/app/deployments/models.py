# encoding:UTF-8
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.models import TimeStampedModel

from hubs.models import Hub
from sensors.models import Sensor, SensorReading, Channel


class Deployment(TimeStampedModel):
    client_name = models.CharField(max_length=255)
    address_line_one = models.CharField(max_length=255)
    post_code = models.CharField(max_length=255)
    notes = models.TextField(null=True, blank=True)

    photo = models.ImageField(_('Header Image'), upload_to='deployment_photos', null=True, blank=True)

    gas_pence_per_kwh = models.FloatField(default=0)
    elec_pence_per_kwh = models.FloatField(default=0)

    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)

    hub = models.OneToOneField(Hub, blank=True, null=True)

    sensors = models.ManyToManyField(Sensor, through='DeploymentSensor')

    def __unicode__(self):
        return self.client_name

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

        for sensor in self.sensor_details.all():
            sensor.sensor_readings.all().delete()

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


class DeploymentChannelCost(TimeStampedModel):
    deployment = models.ForeignKey(Deployment)
    channel = models.ForeignKey(Channel)
    cost = models.FloatField()

    class Meta:
        unique_together = ("deployment", "channel")


class DeploymentDataCache(TimeStampedModel):
    deployment = models.OneToOneField(Deployment, primary_key=True)
    data = models.TextField()


class DeploymentAnnotation(TimeStampedModel):
    text = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    layer = models.IntegerField()
    author = models.ForeignKey(User)
    deployment = models.ForeignKey(Deployment)


class DeploymentSensor(TimeStampedModel):
    deployment = models.ForeignKey(Deployment, related_name='sensor_details')
    sensor = models.ForeignKey(Sensor, related_name='deployment_details')

    location = models.CharField(max_length=255, blank=True, null=True)
    sensor_readings = models.ManyToManyField(SensorReading, related_name='deployments', blank=True)

    class Meta:
        verbose_name_plural = "Deployment Sensors"
        unique_together = ("deployment", "sensor")

    def __unicode__(self):
        return '{sensor} for {deployment}'.format(
            sensor=self.sensor, deployment=self.deployment
        )

    @property
    def battery_percentage(self):
        try:
            battery_reading = self.sensor_readings.filter(
                channel__name='BATT').order_by('-timestamp')[0]
            return battery_reading.value
        # return round(battery_reading.value / float(3) * 100)
        except IndexError:
            return False

    @property
    def earliest_reading_date(self):
        return self.sensor_readings.order_by('timestamp')[0].timestamp

    @property
    def latest_reading_date(self):
        try:
            return self.sensor_readings.order_by('-timestamp')[0].timestamp
        except IndexError:
            pass

    @property
    def latest_readings(self):
        latest_readings = []

        for channel in self.sensor.channels.all():
            try:
                reading = self.sensor_readings.filter(channel=channel).order_by('-timestamp')[0]
                latest_readings.append({
                    'channel': channel,
                    'value': reading.value
                })
            except:
                latest_readings.append({
                    'channel': channel
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


class DeploymentSensorReading(models.Model):
    deployment = models.ForeignKey(Deployment, db_index=True)
    sensor = models.ForeignKey(Sensor, db_index=True)
    channel = models.ForeignKey(Channel, db_index=True)
    timestamp = models.FloatField(db_index=True)
    value = models.FloatField(_('value'), default=0)
    important = models.BooleanField(db_index=True, default=True)

    class Meta:
        ordering = ['timestamp']
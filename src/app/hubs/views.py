# encoding:UTF-8
import logging

from datetime import datetime,timedelta
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json
from django.utils import timezone
from django.views.generic import CreateView
from rest_framework import status, serializers, authentication
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, ListAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from chariot import utils
from chariot.mixins import LoginRequiredMixin, BackButtonMixin
from chariot.utils import LOCALE_DATE_FMT
from deployments.models import Deployment, DeploymentSensor, DeploymentDataCache
from graphs.views import generate_data
from hubs.forms import HubCreateForm
from hubs.models import Hub
from hubs.serializers import HubSerializer, HubIDSerializer
from sensors.models import Channel, Sensor, SensorReading
from sensors.serializers import SensorIDSerializer

logger = logging.getLogger(__name__)


class DeploymentSerializer(serializers.ModelSerializer):
    hub = HubIDSerializer()
    sensors = SensorIDSerializer()

    class Meta:
        model = Deployment
        fields = ('id', 'hub', 'sensors')


class DeploymentListView(ListAPIView):
    model = Deployment
    serializer_class = DeploymentSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def get_queryset(self):
        return Deployment.objects.filter(end_date__isnull=True)


def get_token(request, mac_address):
    try:
        hub = Hub.objects.get(mac_address=mac_address)
        token = Token.objects.latest('created')
        return HttpResponse(json.dumps({'token': token.key}), content_type='application/json')
    except Hub.DoesNotExist, Token.DoesNotExist:
        return HttpResponse(status=404)


class HubPingView(UpdateAPIView):
    model = Hub
    serializer_class = HubSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def get_object(self, queryset=None):
        mac_address = utils.decode_mac_address(self.kwargs.get('mac_address'))

        hub = get_object_or_404(Hub, mac_address=mac_address)

        # May raise a permission denied
        self.check_object_permissions(self.request, hub)

        hub.ping()
        hub.save()

        return hub


class SensorListView(ListAPIView):
    model = Sensor
    serializer_class = SensorIDSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def get_queryset(self):
        mac_address = utils.decode_mac_address(self.kwargs.get('mac_address'))

        hub = get_object_or_404(Hub, mac_address=mac_address)

        return hub.sensors


class SensorReadingSerializer(serializers.ModelSerializer):
    hub = serializers.IntegerField()
    timestamp = serializers.DateTimeField(default=timezone.now)

    class Meta:
        model = SensorReading
        fields = ('channel', 'sensor', 'value', 'hub', 'timestamp')

    def save(self, **kwargs):
        """
        Save the deserialized object and return it.
        """
        # Clear cached _data, which may be invalidated by `save()`
        self._data = None

        if isinstance(self.object, list):
            [self.save_object(item, **kwargs) for item in self.object]

            if self.object._deleted:
                [self.delete_object(item) for item in self.object._deleted]
        else:
            self.save_object(self.object, **kwargs)

        return self.object

    def validate(self, attrs):
        try:
            hub = Hub.objects.get(id=attrs['hub'])
        except:
            raise serializers.ValidationError("Hub " + attrs['hub'] + " not found")

        if hub.deployment is None:
            raise serializers.ValidationError("No Deployment associated with hub " + hub)

        if hub.deployment.end_date is not None:
            raise serializers.ValidationError("Deployment " + hub.deployment + " ended")

        # TODO Check sensor in deployment & channel in sensor

        return attrs


class SensorReadingCreateView(CreateAPIView):
    model = SensorReading
    serializer_class = SensorReadingSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def create(self, request, *args, **kwargs):
        sensor = get_object_or_404(Sensor, identifier=request.DATA['sensor'])
        channel = get_object_or_404(Channel, name=request.DATA['channel'])

        hub_mac_address = utils.decode_mac_address(request.DATA['hub'])
        hub = Hub.objects.get(mac_address=hub_mac_address)

        data = {
            'channel': channel.id,
            'hub': hub.id,
            'sensor': sensor.pk,
            'value': request.DATA['value']
        }

        if 'timestamp' in request.DATA:
            data['timestamp'] = request.DATA['timestamp']

        serializer = self.get_serializer(data=data, files=request.FILES)

        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = self.get_success_headers(serializer.data)

            deployment_details = DeploymentSensor.objects.get(
                deployment=hub.deployment,
                sensor=sensor
            )

            deployment_details.sensor_readings.add(self.object)

            try:
                cached = DeploymentDataCache.objects.get(deployment=hub.deployment)
                cache_time = cached.created
                if (self.object.timestamp - cache_time) > timedelta(hours=1):
                    cached.delete()
            except DeploymentDataCache.DoesNotExist:
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HubCreateView(LoginRequiredMixin, BackButtonMixin, CreateView):
    form_class = HubCreateForm
    model = Hub
    template_name = 'sensors/device_create.html'

    def get_success_url(self):
        return reverse('devices')

    def get_back_url(self):
        return reverse('devices')


class DataView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, pk, format=None):
        out = []
        deployment = Deployment.objects.get(pk=pk)

        show_hidden = 'channels' in request.GET and request.GET['channels'].lower() == 'all'
        simplify = 'simplify' not in request.GET or request.GET['simplify'].lower() != 'false'
        if 'start' in request.GET:
            start = datetime.strptime(request.GET['start'], LOCALE_DATE_FMT)
        else:
            start = None

        if 'end' in request.GET:
            end = datetime.strptime(request.GET['end'], LOCALE_DATE_FMT)
        else:
            end = None

        sensor_list = None
        if 'sensors' in request.GET:
            sensor_list = request.GET['sensors'].split(",")

        channel_list = None
        show_hidden = False
        if 'channels' in request.GET:
            if request.GET['channels'].lower() == 'all':
                show_hidden = True
            else:
                channel_list = request.GET['channels'].split(",")

        for sensor in deployment.sensors.all():
            if not sensor_list or str(sensor.id) in sensor_list:
                sensor_obj = {
                    'name': sensor.name,
                    'location': sensor.deployment_details.filter(deployment__pk=pk)[0].location,
                    'channels': [],
                    'id': sensor.id}
                for channel in sensor.channels.all():
                    if (channel_list and channel.name in channel_list) or (not channel_list and (not channel.hidden or show_hidden)):
                        channel_obj = {
                            'id': channel.id,
                            'name': channel.name,
                            'friendly_name': channel.friendly_name,
                            'data': generate_data(deployment, sensor, channel, simplify, start, end),
                            'units': channel.units}
                        sensor_obj['channels'].append(channel_obj)

                if sensor_list or len(sensor_obj['channels']) > 0:
                    out.append(sensor_obj)

        return HttpResponse(json.dumps(out), content_type='application/json')
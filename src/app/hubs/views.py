# encoding:UTF-8
import logging

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

from chariot import utils
from chariot.mixins import LoginRequiredMixin, BackButtonMixin
from deployments.models import Deployment, DeploymentSensor
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

# encoding:UTF-8
import logging

from django.utils import timezone
from datetime import datetime, timedelta
from chariot.influx import influx
from datetime import datetime
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json
from django.views.generic import CreateView
from rest_framework import status, serializers, authentication
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from chariot import utils
from chariot.mixins import LoginRequiredMixin, BackButtonMixin
from chariot.utils import LOCALE_DATE_FMT
from deployments.models import Deployment, DeploymentSensor, DeploymentDataCache
from graphs.views import generate_data
from hubs.forms import HubCreateForm
from hubs.models import Hub
from sensors.models import Sensor
from sensors.serializers import SensorIDSerializer

logger = logging.getLogger(__name__)


class DeploymentSensorIDSerializer(serializers.ModelSerializer):
    sensor = SensorIDSerializer()

    class Meta:
        model = DeploymentSensor
        fields = ('sensor', 'cost', 'location')


class DeploymentSerializer(serializers.ModelSerializer):
    hub = serializers.PrimaryKeyRelatedField(read_only=True)
    sensors = DeploymentSensorIDSerializer()

    class Meta:
        model = Deployment
        fields = ('id', 'hub', 'sensors')


class DeploymentListView(ListAPIView):
    model = Deployment
    serializer_class = DeploymentSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def get_queryset(self):
        return Deployment.objects.filter(end_date__isnull=True)


class DeploymentView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get_object(self, pk):
        try:
            return Deployment.objects.get(pk=pk)
        except Deployment.DoesNotExist:
            raise HttpResponse(status=404)

    def get(self, request, pk, format=None):
        deployment = self.get_object(pk)
        serializer = DeploymentSerializer(deployment)
        return Response(serializer.data)


def get_token(request, id):
    try:
        hub = Hub.objects.get(id=id)
        token = Token.objects.latest('created')
        return HttpResponse(json.dumps({'token': token.key, 'deployment': hub.deployment.pk}), content_type='application/json')
    except Hub.DoesNotExist, Token.DoesNotExist:
        return HttpResponse(status=404)


class HubPingView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def put(self, request, id, format=None):
        mac_address = utils.decode_mac_address(id)

        hub = get_object_or_404(Hub, id=mac_address)

        # May raise a permission denied
        self.check_object_permissions(self.request, hub)

        hub.ping()
        hub.save()

        return Response("success", status=status.HTTP_200_OK)


class SensorListView(ListAPIView):
    model = Sensor
    serializer_class = SensorIDSerializer
    authentication_classes = (authentication.TokenAuthentication,)

    def get_queryset(self):
        mac_address = utils.decode_mac_address(self.kwargs.get('mac_address'))

        hub = get_object_or_404(Hub, id=mac_address)

        return hub.sensors


class SensorReading(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request):
        reading = {
            "measurement": request.DATA['channel'],
            "tags": {
                "sensor": request.DATA['sensor'],
                "deployment": long(request.DATA['deployment'])
            },
            "fields": {
                "value": float(request.DATA['value'])
            }
        }
        logger.info(reading)
        if 'timestamp' in request.DATA:
            reading['time'] = request.DATA['timestamp']
        if influx.write_points([reading]):
            try:
                cached = DeploymentDataCache.objects.get(deployment=int(request.DATA['deployment']))
                cache_time = cached.created
                if (timezone.now() - cache_time) > timedelta(minutes=20):
                    cached.delete()
            except DeploymentDataCache.DoesNotExist:
                pass

            return Response(reading, status=status.HTTP_201_CREATED)
        return Response("failed", status=status.HTTP_400_BAD_REQUEST)


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
            if not sensor_list or sensor.sensor.id in sensor_list:
                sensor_obj = {
                    'name': sensor.sensor.name,
                    'location': sensor.location,
                    'channels': [],
                    'id': sensor.sensor.id}
                for channel in sensor.sensor.channels.all():
                    if (channel_list and channel.name in channel_list) or (not channel_list and (not channel.hidden or show_hidden)):
                        channel_obj = {
                            'id': channel.id,
                            'name': channel.name,
                            'data': generate_data(deployment, sensor.sensor, channel, simplify, start, end),
                            'units': channel.units}
                        sensor_obj['channels'].append(channel_obj)

                if sensor.cost > 0:
                    sensor_obj['cost'] = sensor.cost

                if sensor_list or len(sensor_obj['channels']) > 0:
                    out.append(sensor_obj)

        return HttpResponse(json.dumps(out), content_type='application/json')
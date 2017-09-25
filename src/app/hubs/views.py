# encoding:UTF-8
import logging

from chariot.influx import influx
from datetime import datetime
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
import json
from django.views.generic import CreateView
from rest_framework import status, serializers, authentication
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from chariot import utils
from chariot.mixins import LoginRequiredMixin, BackButtonMixin
from chariot.utils import LOCALE_DATE_FMT
from deployments.models import Deployment, DeploymentSensor
from graphs.views import generate_data, last
from hubs.forms import HubCreateForm
from hubs.models import Hub
from sensors.models import Sensor
from sensors.serializers import SensorIDSerializer

logger = logging.getLogger(__name__)


class DeploymentSensorIDSerializer(serializers.ModelSerializer):
    sensor = SensorIDSerializer()

    class Meta:
        model = DeploymentSensor
        fields = ('sensor', 'cost', 'location', 'nearest_thermostat', 'room_height', 'room_area')


class DeploymentSerializer(serializers.ModelSerializer):
    hub = serializers.PrimaryKeyRelatedField(read_only=True)
    sensors = DeploymentSensorIDSerializer(many=True)

    class Meta:
        model = Deployment
        fields = ('id', 'hub', 'sensors',
                  'boiler_manufacturer', 'boiler_model', 'boiler_output', 'boiler_efficiency',
                  'boiler_type', 'boiler_thermostat', 'building_area', 'building_height')


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
        return JsonResponse({'token': token.key, 'deployment': hub.deployment.pk})
    except Hub.DoesNotExist:
        return HttpResponse(status=404)
    except Token.DoesNotExist:
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
        hub_mac_address = utils.decode_mac_address(request.data['hub'])
        hub = Hub.objects.get(id=hub_mac_address)

        reading = {
            "measurement": request.data['channel'],
            "tags": {
                "sensor": request.data['sensor'],
                "deployment": hub.deployment.pk
            },
            "fields": {
                "value": float(request.data['value'])
            }
        }
        logger.info(reading)
        if 'timestamp' in request.data:
            reading['time'] = request.data['timestamp']
        if influx.write_points([reading]):
            return Response(reading, status=status.HTTP_201_CREATED)
        return Response("failed", status=status.HTTP_400_BAD_REQUEST)


class DeploymentPrediction(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def put(self, request, pk):
        prediction_json = json.loads(request.body)
        for prediction in prediction_json:
            try:
                deployment_id = prediction['Deployment_Id']
                deployment = Deployment.objects.get(pk=deployment_id)
                deployment.prediction = json.dumps(prediction)
                deployment.save()
            except Deployment.DoesNotExist:
                return HttpResponse(status=404)

        return Response("success", status=status.HTTP_200_OK)


class HubCreateView(LoginRequiredMixin, BackButtonMixin, CreateView):
    form_class = HubCreateForm
    model = Hub
    template_name = 'sensors/device_create.html'

    def get_success_url(self):
        return reverse('devices')

    def get_back_url(self):
        return reverse('devices')


class LatestDataView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, pk, format=None):
        deployment = Deployment.objects.get(pk=pk)
        result = []

        for sensor in deployment.sensors.all():
            sensor_obj = {'id': sensor.id, 'channels': []}
            for channel in sensor.sensor.channels.all():
                value = last(deployment, sensor, channel)
                if value.has_data():
                    channel_obj = {'id': channel.id, 'value': value.data}
                    sensor_obj['channels'].append(channel_obj)
            if sensor_obj['channels']:
                result.append(sensor_obj)

        return JsonResponse(result, safe=False)


class DataView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, pk, format=None):
        aggregate = None
        sensors = None
        channels = None
        start = None
        end = None

        if 'sensors' in request.GET:
            sensors = request.GET['sensors'].split(",")

        if 'channels' in request.GET:
            if request.GET['channels'].lower() == 'all':
                channels = 'all'
            else:
                channels = request.GET['channels'].split(",")

        if 'start' in request.GET:
            start = datetime.strptime(request.GET['start'], LOCALE_DATE_FMT)

        if 'end' in request.GET:
            end = datetime.strptime(request.GET['end'], LOCALE_DATE_FMT)

        simplify = 'simplify' not in request.GET or request.GET['simplify'].lower() != 'false'
        if 'aggregate' in request.GET:
            aggregate = request.GET['aggregate']

        return StreamingHttpResponse(generate_data(pk, sensors, channels, simplify, start, end, aggregate),
                                     content_type="application/json")

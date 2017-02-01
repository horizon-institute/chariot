import datetime
import time

from django.core.urlresolvers import reverse
from django.db.models import Avg, Max, Min
from django.http import Http404, HttpResponseBadRequest
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import DetailView

import simplify
from chariot import utils
from chariot.mixins import BackButtonMixin, LoginRequiredMixin
from deployments.models import Deployment, DeploymentAnnotation, DeploymentSensor, DeploymentDataCache
from sensors.forms import IntervalForm
from sensors.models import Channel


def generate_stats(deployment, sensor, channel, start, end):
    sensor_deployment = DeploymentSensor.objects.get(
        deployment=deployment,
        sensor=sensor
    )
    return sensor_deployment.sensor_readings.filter(channel=channel,
                                                    timestamp__range=(start, end)
                                                    ).aggregate(Avg('value'),
                                                                Max('value'),
                                                                Min('value'))


def generate_data(deployment, sensor, channel, filter=True, start=None, end=None):
    sensor_deployment = DeploymentSensor.objects.get(
        deployment=deployment,
        sensor=sensor
    )

    if start:
        if end:
            query = sensor_deployment.sensor_readings.filter(channel=channel,
                                                             timestamp__range=(start, end))
        else:
            query = sensor_deployment.sensor_readings.filter(channel=channel,
                                                             timestamp__gte=start)
    elif end:
        query = sensor_deployment.sensor_readings.filter(channel=channel,
                                                         timestamp__lte=end)
    else:
        query = sensor_deployment.sensor_readings.filter(channel=channel)

    readings = query.values('timestamp', 'value')

    if readings.count() > 10 and filter:
        minmax = query.aggregate(Max('value'),
                                 Min('value'))

        time_min = int(1000 * time.mktime(readings[0]['timestamp'].timetuple()))
        value_range = minmax['value__max'] - minmax['value__min']
        for reading in readings:
            reading['t'] = int(1000 * time.mktime(reading['timestamp'].timetuple()))
            reading['x'] = (reading['t'] - time_min) / 50000
            reading['y'] = (reading['value'] - minmax['value__min']) * 1000 / value_range

        result = simplify.simplify(readings, 10)

        for reading in result:
            del reading['timestamp']
            del reading['x']
            del reading['y']

        return result

    for reading in readings:
        reading['t'] = int(1000 * time.mktime(reading['timestamp'].timetuple()))
        del reading['timestamp']

    return list(readings)


def get_all_data(request, pk):
    try:
        cache = DeploymentDataCache.objects.get(pk=pk)
    except DeploymentDataCache.DoesNotExist:
        deployment = Deployment.objects.get(pk=pk)
        out = []

        show_hidden = 'channels' in request.GET and request.GET['channels'].lower() == 'all'
        for sensor in deployment.sensors.all():
            sensor_obj = {
                'name': sensor.name,
                'location': sensor.deployment_details.filter(deployment__pk=pk)[0].location,
                'channels': [],
                'id': sensor.id}
            for channel in sensor.channels.all():
                if channel.hidden and not show_hidden:
                    continue
                channel_obj = {
                    'id': channel.id,
                    'name': channel.name,
                    'friendly_name': channel.friendly_name,
                    'data': generate_data(deployment, sensor, channel),
                    'units': channel.units}
                sensor_obj['channels'].append(channel_obj)

            out.append(sensor_obj)

        cache = DeploymentDataCache(deployment=deployment, data=json.dumps(out))
        cache.save()

    annotations = DeploymentAnnotation.objects.filter(deployment=pk)
    annotationList = []
    for annotation in annotations:
        obj = utils.to_dict(annotation)
        annotationList.append(obj)

    out = "{\"sensors\": " + cache.data + ", \"annotations\": " + json.dumps(annotationList) + "}"

    return HttpResponse(out, content_type='application/json')


def get_data(request, pk, sensor, channel_name):
    form = IntervalForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(utils.get_json_error(dict(form.errors)))

    start = form.cleaned_data['start']
    end = form.cleaned_data['end']

    sensor_deployment = DeploymentSensor.objects.get(
        deployment=pk,
        sensor=sensor
    )
    channel = Channel.objects.get(name=channel_name)

    querybase = sensor_deployment.sensor_readings.filter(channel=channel,
                                                         timestamp__range=(start, end)
                                                         )

    readings = querybase.values('timestamp', 'value')

    result = {}
    if readings.count() > 2:
        minmax = querybase.aggregate(Max('value'),
                                     Min('value'))

        time_min = int(1000 * time.mktime(readings[0]['timestamp'].timetuple()))
        time_max = int(1000 * time.mktime(readings[readings.count() - 1]['timestamp'].timetuple()))
        time_range = time_max - time_min
        value_range = minmax['value__max'] - minmax['value__min']
        for reading in readings:
            reading['t'] = int(1000 * time.mktime(reading['timestamp'].timetuple()))
            reading['x'] = (reading['t'] - time_min) * 1000 / time_range
            reading['y'] = (reading['value'] - minmax['value__min']) * 1000 / value_range

        result['data'] = simplify.simplify(readings, 20, False)

        for reading in result['data']:
            del reading['timestamp']
            del reading['x']
            del reading['y']

    return HttpResponse(json.dumps(result), content_type='application/json')


def get_devices(request, pk):
    deployment = Deployment.objects.get(pk=pk)
    annotations = DeploymentAnnotation.objects.filter(deployment=pk)

    form = IntervalForm(request.GET)
    if not form.is_valid():
        print form.errors
        return HttpResponseBadRequest("Invalid Parameters")
    start = form.cleaned_data['start']
    end = form.cleaned_data['end']

    out = {'sensors': [], 'annotations': []}

    for annotation in annotations:
        obj = utils.to_dict(annotation)
        out['annotations'].append(obj)

    show_hidden = 'channels' in request.GET and request.GET['channels'].lower() == 'all'
    for sensor in deployment.sensors.all():
        sensor_obj = {
            'name': sensor.name,
            'location': sensor.deployment_details.filter(deployment__pk=pk)[0].location,
            'channels': [],
            'id': sensor.id}
        for channel in sensor.channels.all():
            if channel.hidden and not show_hidden:
                continue
            channel_obj = {
                'id': channel.id,
                'name': channel.name,
                'friendly_name': channel.friendly_name,
                'stats': generate_stats(deployment, sensor, channel, start, end),
                'units': channel.units}
            sensor_obj['channels'].append(channel_obj)

        out['sensors'].append(sensor_obj)
    return HttpResponse(json.dumps(out), content_type='application/json')


class DeploymentGraphView(LoginRequiredMixin, BackButtonMixin, DetailView):
    model = Deployment
    template_name = 'graphs/deployment_graph.html'

    def get_back_url(self):
        return reverse('deployments:update', args=(self.object.id,))

    def get_context_data(self, **kwargs):
        context = super(DeploymentGraphView, self).get_context_data(**kwargs)
        deployment = self.get_object()

        if deployment.start_date is None:
            raise Http404("Deployment not started")

        context['dateTo'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context['dateFrom'] = deployment.start_date.strftime("%Y-%m-%d %H:%M:%S")
        return context

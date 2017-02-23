import datetime

from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.generic import DetailView

import simplify
from chariot.influx import select, select_from
from chariot import utils
from chariot.mixins import BackButtonMixin, LoginRequiredMixin
from deployments.models import Deployment, DeploymentAnnotation, DeploymentDataCache


def generate_data(deployment, sensor, channel, filter=True, start=None, end=None):
    query = select_from(channel.id).where('deployment').eq(deployment.pk).where('sensor').eq(sensor.id)
    if start:
        query = query.where('time').gte(start)

    if end:
        query = query.where('time').lte(end)

    readings = query.fetch()
    if len(readings) > 10 and filter:
        min_max = select('MIN').select('MAX').from_table(channel.id).where('deployment').eq(deployment.pk).fetch_one()

        time_min = readings[0]['time']
        value_range = min_max['max'] - min_max['min']
        for reading in readings:
            reading['x'] = (reading['time'] - time_min) / 50000
            reading['y'] = (reading['value'] - min_max['min']) * 1000 / value_range

        result = simplify.simplify(readings, 1)

        for reading in result:
            del reading['x']
            del reading['y']

        return result

    return readings


def get_all_data(request, pk):
    try:
        cache = DeploymentDataCache.objects.get(pk=pk)
    except DeploymentDataCache.DoesNotExist:
        deployment = Deployment.objects.get(pk=pk)
        out = []

        show_hidden = 'channels' in request.GET and request.GET['channels'].lower() == 'all'
        for sensor in deployment.sensors.all():
            sensor_obj = {
                'name': sensor.sensor.name,
                'location': sensor.location,
                'cost': sensor.cost,
                'channels': [],
                'id': sensor.sensor.id}
            for channel in sensor.sensor.channels.all():
                if channel.hidden and not show_hidden:
                    continue
                channel_obj = {
                    'id': channel.id,
                    'name': channel.name,
                    'data': generate_data(deployment, sensor.sensor, channel),
                    'units': channel.units}
                sensor_obj['channels'].append(channel_obj)

            if sensor.cost > 0:
                sensor_obj['cost'] = sensor.cost

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

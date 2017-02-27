import datetime
import json

from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import StreamingHttpResponse
from django.views.generic import DetailView

from chariot import utils
from chariot.influx import select_from
from chariot.mixins import BackButtonMixin, LoginRequiredMixin
from deployments.models import Deployment, DeploymentAnnotation
from graphs import simplify


def query(deployment, sensor, channel, start=None, end=None):
    query = select_from(channel.id).where('deployment').eq(deployment.pk).where('sensor').eq(sensor.id)
    if start:
        query = query.where('time').gte(start)

    if end:
        query = query.where('time').lte(end)

    return query.fetch()


def generate_data(deploymentID):
    try:
        yield '{"sensors":['
        deployment = Deployment.objects.get(pk=deploymentID)
        first_sensor = True
        for sensor in deployment.sensors.all():
            if first_sensor:
                first_sensor = False
            else:
                yield ','
            yield '{"id":' + sensor.sensor.id + ','
            yield '"name":"' + sensor.sensor.name + '",'
            yield '"location":"' + sensor.location + '",'
            if sensor.cost:
                yield '"cost":' + str(sensor.cost) + ','
            yield '"channels":['

            first_channel = True
            for channel in sensor.sensor.channels.all():
                if channel.hidden:# and not show_hidden:
                    continue
                response = query(deployment, sensor.sensor, channel)
                data = response.list()
                first_value = True
                while len(data) > 0:
                    data = simplify.simplify(data, 1)
                    for value in data:
                        if first_value:
                            first_value = False
                            if first_channel:
                                first_channel = False
                            else:
                                yield ','
                            yield '{"id":"' + channel.id + '",'
                            yield '"name":"' + channel.name + '",'
                            yield '"units":"' + channel.units + '",'
                            yield '"data":['
                        else:
                            yield ','
                        yield '{"time":' + str(value['time']) + ','
                        yield '"value":' + str(value['value']) + '}'
                    if response.is_partial():
                        response = response.next()
                        data = response.list()
                    else:
                        data = []
                        yield ']}'

            yield ']}'
        yield '],'
        yield '"annotations":['
        annotations = DeploymentAnnotation.objects.filter(deployment=deploymentID)
        first_annotation = True
        for annotation in annotations:
            if first_annotation:
                first_annotation = False
            else:
                yield ','
            obj = utils.to_dict(annotation)
            yield json.dumps(obj)
        yield ']}'
    except Exception as e:
        yield e


def get_all_data(request, pk):
    return StreamingHttpResponse(generate_data(pk), content_type="application/json")


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

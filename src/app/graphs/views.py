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

    query = query.limit(10000)

    return query.fetch()


def generate_data(deployment_id, sensors=None, channels=None, simplified=True, start=None, end=None):
    try:
        yield '{"sensors":['
        deployment = Deployment.objects.get(pk=deployment_id)
        first_sensor = True
        for sensor in deployment.sensors.all():
            if sensors and sensor.sensor.id not in sensors:
                continue
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
                if channels != 'all' and (channel.hidden or (channels and channel.id not in channels)):
                    continue
                response = query(deployment, sensor.sensor, channel, start, end)
                first_value = True
                timestamp = 0
                while response.has_data():
                    if simplified:
                        data = simplify.simplify(response.data, 0.2)
                    else:
                        data = response.data
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
                        response.next()
                    else:
                        break

                if not first_value:
                    yield ']}'

            yield ']}'
        yield '],'
        yield '"annotations":['
        annotations = DeploymentAnnotation.objects.filter(deployment=deployment_id)
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

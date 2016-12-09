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
from deployments.models import Deployment, DeploymentAnnotation, DeploymentSensor
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


def get_data(request, pk, sensor, channel_name):
	sensor_deployment = DeploymentSensor.objects.get(
		deployment=pk,
		sensor=sensor
	)
	channel = Channel.objects.get(name=channel_name)
	form = IntervalForm(request.GET)
	if not form.is_valid():
		return HttpResponseBadRequest(utils.get_json_error(dict(form.errors)))

	start = form.cleaned_data['start']
	end = form.cleaned_data['end']

	readings = sensor_deployment.sensor_readings.filter(channel=channel,
	                                                    timestamp__range=(start, end)
	                                                    ).values('timestamp', 'value')

	result = {}
	if readings.count() > 2:
		reading_min = float('inf')
		reading_max = float('-inf')
		for reading in readings:
			reading['t'] = 1000 * time.mktime(reading['timestamp'].timetuple())
			if reading['value'] > reading_max:
				reading_max = reading['value']
			if reading['value'] < reading_min:
				reading_min = reading['value']
			del reading['timestamp']

		smoothing = (reading_max - reading_min) / 20.0
		result['data'] = simplify.simplify(readings, smoothing, False)

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

	out = {'sensors': [], 'annotations': [], 'stats': []}

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

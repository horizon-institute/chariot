from django import forms
from django.forms import TextInput

from hubs.models import Hub
from sensors.models import Sensor
from .models import Deployment, DeploymentSensor, DeploymentAnnotation
from crispy_forms.helper import FormHelper
from crispy_forms.layout import *


class NumberInput(TextInput):
	input_type = 'number'


class DeploymentAddHubForm(forms.ModelForm):
	class Meta:
		fields = ['hub']
		model = Deployment
		widgets = {
			'hub': forms.HiddenInput()
		}

	def __init__(self, *args, **kwargs):
		super(DeploymentAddHubForm, self).__init__(*args, **kwargs)

		self.fields['hub'].label = "Hub Identifier"

	def clean_hub(self):
		hub = self.cleaned_data['hub']

		if self.instance.hub:
			raise forms.ValidationError(
				"There is already a hub assigned to this deployment.")

		try:
			old_deployment = hub.deployment
			old_deployment.hub = None
			old_deployment.save()
		except (AttributeError, Deployment.DoesNotExist):
			pass

		return hub


class DeploymentAnnotationForm(forms.ModelForm):
	class Meta:
		fields = ['start', 'end', 'layer', 'deployment', 'text']
		model = DeploymentAnnotation

	start = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M:%S'])
	end = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M:%S'])


class DeploymentUpdateForm(forms.ModelForm):
	gas_pence_per_kwh = forms.Field(widget=NumberInput, label='Gas Cost (pence per KWh)')
	elec_pence_per_kwh = forms.Field(widget=NumberInput, label='Electricity Cost (pence per KWh)')
	address_line_one = forms.CharField(label='First Line of Address')

	def __init__(self, *args, **kwargs):
		super(DeploymentUpdateForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.field_template = 'chariot/field.html'
		self.helper.layout = Layout(
			'photo',
			'client_name',
			'address_line_one',
			'post_code',
			'elec_pence_per_kwh',
			'gas_pence_per_kwh',
			'notes',
			Submit(
				'save', 'Save Deployment',
				css_class='mdl-button mdl-js-button button_right mdl-button--raised mdl-button--colored')
		)

	class Meta:
		fields = [
			'client_name', 'photo', 'address_line_one', 'post_code', 'elec_pence_per_kwh',
			'gas_pence_per_kwh', 'notes']
		model = Deployment


class DeploymentCreateForm(forms.ModelForm):
	gas_pence_per_kwh = forms.Field(widget=NumberInput, label='Gas Cost (pence per KWh)')
	elec_pence_per_kwh = forms.Field(widget=NumberInput, label='Electricity Cost (pence per KWh)')
	address_line_one = forms.CharField(label='First Line of Address')
	hub = forms.ModelChoiceField(queryset=Hub.objects.filter(deployment__isnull=True), empty_label=None)

	def __init__(self, *args, **kwargs):
		super(DeploymentCreateForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.field_template = 'chariot/field.html'
		self.helper.layout = Layout(
			'photo',
			'client_name',
			'hub',
			'address_line_one',
			'post_code',
			'elec_pence_per_kwh',
			'gas_pence_per_kwh',
			'notes',
			Submit(
				'save', 'Create Deployment',
				css_class='mdl-button mdl-js-button button_right mdl-button--raised mdl-button--colored')
		)

	def save(self, commit=True):
		# TODO Check hub

		instance = super(DeploymentCreateForm, self).save(commit=False)
		if commit:
			instance.save()

		# Create DeploymentSensors for all default sensors
		sensors = Sensor.objects.filter(default=True)
		for sensor in sensors:
			sensor_deployment = DeploymentSensor(sensor=sensor, deployment=instance, location=sensor.name)
			sensor_deployment.save()

		return instance

	class Meta:
		fields = [
			'client_name', 'photo', 'hub', 'address_line_one', 'post_code', 'elec_pence_per_kwh',
			'gas_pence_per_kwh', 'notes']
		model = Deployment


class DeploymentEndForm(forms.ModelForm):
	class Meta:
		fields = ['id']
		model = Deployment

	def save(self, commit=True):
		self.instance.end()


class DeploymentStartForm(forms.ModelForm):
	class Meta:
		fields = ['id']
		model = Deployment

	def save(self, commit=True):
		self.instance.start()


class DeploymentUpdatePhotoForm(forms.ModelForm):
	class Meta:
		fields = ['photo', ]
		model = Deployment


class DeploymentSensorLocationUpdateForm(forms.ModelForm):
	class Meta:
		fields = ['location']
		model = DeploymentSensor


class DeploymentSensorCreateForm(forms.ModelForm):
	class Meta:
		fields = ['deployment', 'sensor', 'location']
		model = DeploymentSensor
		widgets = {
			'deployment': forms.HiddenInput(),
			'sensor': forms.HiddenInput()
		}

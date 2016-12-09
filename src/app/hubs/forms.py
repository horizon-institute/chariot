from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import *
from django.core.exceptions import ValidationError

from hubs.models import Hub

import re


class HubCreateForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(HubCreateForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.field_template = 'chariot/field.html'
		self.helper.layout = Layout(
			'name',
			'mac_address',
			Submit(
				'add_hub', 'Create Hub',
				css_class='mdl-button mdl-js-button button_right mdl-button--raised mdl-button--colored')
		)

	def clean_mac_address(self):
		mac_address = self.cleaned_data['mac_address'].lower().replace("-", ":")
		if not re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address):
			raise ValidationError(mac_address + " is not a valid MAC Address")
		if Hub.objects.filter(mac_address=mac_address).exists():
			raise ValidationError("A Hub with the MAC Address " + mac_address + " already exists")
		return mac_address

	class Meta:
		fields = ['name', 'mac_address']
		model = Hub

# encoding:UTF-8
from datetime import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _

from chariot.utils import DATE_FMTS


class JSTimestampField(forms.fields.IntegerField):
	default_error_messages = {
		'invalid': _(u'Enter a valid timestamp.'),
	}

	def to_python(self, value):
		"""
		Validates that float() can be called on the input. Returns the result
		of float(). Returns None for empty values.
		"""
		value = super(forms.fields.IntegerField, self).to_python(value)
		if value in forms.fields.validators.EMPTY_VALUES:
			return None
		if self.localize:
			value = forms.fields.formats.sanitize_separators(value)
		try:
			value = float(value)
			value = datetime.fromtimestamp(value / 1000)
		except (ValueError, TypeError):
			raise forms.fields.ValidationError(self.error_messages['invalid'])
		return value


class RawDataForm(forms.Form):
	# start and end are passed as timestamps
	value = forms.FloatField()
	key = forms.CharField(max_length=32)


class IntervalForm(forms.Form):
	# start and end are passed as timestamps
	start = forms.DateTimeField(input_formats=DATE_FMTS)
	end = forms.DateTimeField(input_formats=DATE_FMTS)


class SampledIntervalForm(IntervalForm):
	sampling_interval = forms.IntegerField(min_value=0)
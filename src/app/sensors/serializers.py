from rest_framework import serializers

from sensors.models import Sensor, Channel


class ChannelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Channel
		fields = ('friendly_name', 'name', 'units')


class SensorIDSerializer(serializers.ModelSerializer):
	channels = ChannelSerializer()

	class Meta:
		model = Sensor
		fields = ('id', 'identifier', 'channels')
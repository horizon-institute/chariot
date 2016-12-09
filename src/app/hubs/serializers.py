from rest_framework import serializers

from .models import Hub


class HubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = ('id', 'external_network_address', 'network_address')


class HubIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hub
        fields = ('id', 'mac_address')


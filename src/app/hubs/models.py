import binascii

from django.conf import settings
from django.db import models
from django.utils import timezone

from django_extensions.db.models import TimeStampedModel

from django.utils.translation import ugettext_lazy as _


class Hub(TimeStampedModel):
    """
    A virtual version on the Raspberry Pi and what sensors are attached to it.
    """
    name = models.CharField(_('Name'), max_length=255)
    mac_address = models.CharField(_('MAC Address'), max_length=255)
    external_network_address = models.GenericIPAddressField(
        blank=True, null=True)
    network_address = models.GenericIPAddressField(blank=True, null=True)
    online_since = models.DateTimeField(blank=True, null=True)
    last_ping = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return '{name} with MAC address {mac_address}'.format(
            name=self.name, mac_address=self.mac_address
        )

    @property
    def connection_status(self):
        if self.online_since:
            now = timezone.now()

            time_difference = now - self.last_ping

            if time_difference.seconds < settings.HUB_OFFLINE_TIME:

                time_online = now - self.online_since

                one_hour_in_seconds = 60 * 60

                if time_online.seconds >= one_hour_in_seconds:
                    time_online_string = '{time} hours'.format(
                        time=divmod(
                            time_online.seconds, one_hour_in_seconds)[0]
                    )

                elif time_online.seconds >= 60:
                    time_online_string = '{time} minutes'.format(
                        time=divmod(
                            time_online.seconds,
                            60)[0]
                    )

                else:
                    time_online_string = '{time} seconds'.format(
                        time=time_online.seconds
                    )

                return True, 'Online', time_online_string

        return False, 'Awaiting Connection'

    @property
    def mac_address_encoded(self):
        return binascii.hexlify(self.mac_address.upper())

    def ping(self):
        now = timezone.now()

        if self.last_ping:
            time_difference = (
                now - self.last_ping)

            if time_difference.seconds > settings.HUB_OFFLINE_TIME:
                self.online_since = now
        else:
            self.online_since = now

        self.last_ping = now

        self.save()

    def save(self, *args, **kwargs):
        self.mac_address = self.mac_address.lower()

        hub = super(Hub, self).save(*args, **kwargs)

        return hub

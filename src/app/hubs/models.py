import binascii

from django.conf import settings
from django.db import models
from django.utils import timezone

from django.utils.translation import ugettext_lazy as _


class Hub(models.Model):
    id = models.CharField(_('MAC Address'), primary_key=True, max_length=255)
    name = models.CharField(_('Name'), max_length=255)
    online_since = models.DateTimeField(blank=True, null=True)
    last_ping = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{name} ({mac_address})'.format(
            name=self.name, mac_address=self.id
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
        return binascii.hexlify(self.id.upper())

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
        self.id = self.id.lower()

        hub = super(Hub, self).save(*args, **kwargs)

        return hub

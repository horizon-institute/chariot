# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-16 12:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0005_deploymentthermostatsetting'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deployment',
            name='boiler_thermostat',
        ),
    ]

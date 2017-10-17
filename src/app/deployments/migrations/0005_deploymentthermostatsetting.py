# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-16 12:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0004_deployment_prediction'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeploymentThermostatSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setting', models.FloatField(default=20)),
                ('time', models.TimeField(default=datetime.time(16, 0))),
                ('days', models.CharField(default='all', max_length=100)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thermostats', to='deployments.Deployment')),
            ],
            options={
                'verbose_name_plural': 'Deployment Thermostat Settings',
            },
        ),
    ]

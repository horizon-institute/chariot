# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-15 14:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0002_load_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='aggregation',
            field=models.CharField(default='2m', max_length=10, verbose_name='Aggregation'),
        ),
    ]

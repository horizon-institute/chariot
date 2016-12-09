# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Channel'
        db.create_table('sensors_channel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('units', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('friendly_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('sensors', ['Channel'])

        # Adding model 'Sensor'
        db.create_table('sensors_sensor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30, db_index=True)),
            ('sensor_type', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('sensors', ['Sensor'])

        # Adding M2M table for field channels on 'Sensor'
        m2m_table_name = db.shorten_name('sensors_sensor_channels')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sensor', models.ForeignKey(orm['sensors.sensor'], null=False)),
            ('channel', models.ForeignKey(orm['sensors.channel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['sensor_id', 'channel_id'])

        # Adding model 'SensorReading'
        db.create_table('sensors_sensorreading', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('sensor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sensors.Sensor'])),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sensors.Channel'])),
            ('value', self.gf('django.db.models.fields.FloatField')(default=0)),
        ))
        db.send_create_signal('sensors', ['SensorReading'])


    def backwards(self, orm):
        # Deleting model 'Channel'
        db.delete_table('sensors_channel')

        # Deleting model 'Sensor'
        db.delete_table('sensors_sensor')

        # Removing M2M table for field channels on 'Sensor'
        db.delete_table(db.shorten_name('sensors_sensor_channels'))

        # Deleting model 'SensorReading'
        db.delete_table('sensors_sensorreading')


    models = {
        'sensors.channel': {
            'Meta': {'object_name': 'Channel'},
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'sensors.sensor': {
            'Meta': {'object_name': 'Sensor'},
            'channels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sensors.Channel']", 'symmetrical': 'False'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sensor_type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'sensors.sensorreading': {
            'Meta': {'ordering': "['timestamp']", 'object_name': 'SensorReading'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sensors.Channel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sensors.Sensor']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'default': '0'})
        }
    }

    complete_apps = ['sensors']
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Deployment'
        db.create_table('deployments_deployment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('client_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('address_line_one', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('post_code', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('gas_pence_per_kwh', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('elec_pence_per_kwh', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('hub', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['hubs.Hub'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('deployments', ['Deployment'])

        # Adding model 'DeploymentChannelCost'
        db.create_table('deployments_deploymentchannelcost', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('deployment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['deployments.Deployment'])),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sensors.Channel'])),
            ('cost', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('deployments', ['DeploymentChannelCost'])

        # Adding unique constraint on 'DeploymentChannelCost', fields ['deployment', 'channel']
        db.create_unique('deployments_deploymentchannelcost', ['deployment_id', 'channel_id'])

        # Adding model 'DeploymentDataCache'
        db.create_table('deployments_deploymentdatacache', (
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('deployment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['deployments.Deployment'], unique=True, primary_key=True)),
            ('data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('deployments', ['DeploymentDataCache'])

        # Adding model 'DeploymentAnnotation'
        db.create_table('deployments_deploymentannotation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('layer', self.gf('django.db.models.fields.IntegerField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('deployment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['deployments.Deployment'])),
        ))
        db.send_create_signal('deployments', ['DeploymentAnnotation'])

        # Adding model 'DeploymentSensor'
        db.create_table('deployments_deploymentsensor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('deployment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sensor_details', to=orm['deployments.Deployment'])),
            ('sensor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='deployment_details', to=orm['sensors.Sensor'])),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('deployments', ['DeploymentSensor'])

        # Adding unique constraint on 'DeploymentSensor', fields ['deployment', 'sensor']
        db.create_unique('deployments_deploymentsensor', ['deployment_id', 'sensor_id'])

        # Adding M2M table for field sensor_readings on 'DeploymentSensor'
        m2m_table_name = db.shorten_name('deployments_deploymentsensor_sensor_readings')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('deploymentsensor', models.ForeignKey(orm['deployments.deploymentsensor'], null=False)),
            ('sensorreading', models.ForeignKey(orm['sensors.sensorreading'], null=False))
        ))
        db.create_unique(m2m_table_name, ['deploymentsensor_id', 'sensorreading_id'])

        # Adding model 'DeploymentSensorReading'
        db.create_table('deployments_deploymentsensorreading', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deployment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['deployments.Deployment'])),
            ('sensor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sensors.Sensor'])),
            ('channel', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sensors.Channel'])),
            ('timestamp', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('value', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('important', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
        ))
        db.send_create_signal('deployments', ['DeploymentSensorReading'])


    def backwards(self, orm):
        # Removing unique constraint on 'DeploymentSensor', fields ['deployment', 'sensor']
        db.delete_unique('deployments_deploymentsensor', ['deployment_id', 'sensor_id'])

        # Removing unique constraint on 'DeploymentChannelCost', fields ['deployment', 'channel']
        db.delete_unique('deployments_deploymentchannelcost', ['deployment_id', 'channel_id'])

        # Deleting model 'Deployment'
        db.delete_table('deployments_deployment')

        # Deleting model 'DeploymentChannelCost'
        db.delete_table('deployments_deploymentchannelcost')

        # Deleting model 'DeploymentDataCache'
        db.delete_table('deployments_deploymentdatacache')

        # Deleting model 'DeploymentAnnotation'
        db.delete_table('deployments_deploymentannotation')

        # Deleting model 'DeploymentSensor'
        db.delete_table('deployments_deploymentsensor')

        # Removing M2M table for field sensor_readings on 'DeploymentSensor'
        db.delete_table(db.shorten_name('deployments_deploymentsensor_sensor_readings'))

        # Deleting model 'DeploymentSensorReading'
        db.delete_table('deployments_deploymentsensorreading')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'deployments.deployment': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Deployment'},
            'address_line_one': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'client_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'elec_pence_per_kwh': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'gas_pence_per_kwh': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'hub': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['hubs.Hub']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'post_code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sensors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['sensors.Sensor']", 'through': "orm['deployments.DeploymentSensor']", 'symmetrical': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        'deployments.deploymentannotation': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'DeploymentAnnotation'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deployment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['deployments.Deployment']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer': ('django.db.models.fields.IntegerField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'deployments.deploymentchannelcost': {
            'Meta': {'unique_together': "(('deployment', 'channel'),)", 'object_name': 'DeploymentChannelCost'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sensors.Channel']"}),
            'cost': ('django.db.models.fields.FloatField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deployment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['deployments.Deployment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'deployments.deploymentdatacache': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'DeploymentDataCache'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'deployment': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['deployments.Deployment']", 'unique': 'True', 'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'deployments.deploymentsensor': {
            'Meta': {'unique_together': "(('deployment', 'sensor'),)", 'object_name': 'DeploymentSensor'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'deployment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sensor_details'", 'to': "orm['deployments.Deployment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'deployment_details'", 'to': "orm['sensors.Sensor']"}),
            'sensor_readings': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'deployments'", 'blank': 'True', 'to': "orm['sensors.SensorReading']"})
        },
        'deployments.deploymentsensorreading': {
            'Meta': {'ordering': "['timestamp']", 'object_name': 'DeploymentSensorReading'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sensors.Channel']"}),
            'deployment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['deployments.Deployment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'important': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'sensor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sensors.Sensor']"}),
            'timestamp': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'default': '0'})
        },
        'hubs.hub': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Hub'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'external_network_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_ping': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mac_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'network_address': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'null': 'True', 'blank': 'True'}),
            'online_since': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
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

    complete_apps = ['deployments']
import urllib2
import json
import pandas as pd
import numpy as np
from chariotanalytics.analytics.analytics_config import *
from datetime import datetime, timedelta
from rest_framework.authtoken.models import Token


class Util:
    @staticmethod
    def smooth(x, window=10):
        df = pd.DataFrame(x)
        df = df.rolling(window).mean()
        df = df.bfill().ffill()
        return df.values.flatten().tolist()

    @staticmethod
    def compute_mse(predictions, targets):
        return np.mean((np.subtract(predictions, targets) ** 2))

    @staticmethod
    def legend_out_right(ax):
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))


class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method
        return urllib2.Request.get_method(self, *args, **kwargs)


class DataLoader:
    @classmethod
    def post_deployment(self,dep_id,jason_data):
        url=APPDEFAULTS['server']['server_url'] + 'deployment/' + str(dep_id) + '/prediction'
        req = MethodRequest(url, method='PUT',data=jason_data)
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)

    @classmethod
    def get_all_deployments(self):
        req = urllib2.Request(APPDEFAULTS['server']['server_url'] + 'deployments' + '&simplify=false')
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def get_deployment_details(self, dep_id):
        req = urllib2.Request(APPDEFAULTS['server']['server_url'] + 'deployment/' + str(dep_id) + '&simplify=false')
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def get_deployment_data(self, dep_id):
        req = urllib2.Request(APPDEFAULTS['server']['server_url'] + 'deployment/' + str(dep_id) + '/data&simplify=false')
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def get_deployment_data_within_range(self, dep_id, start, end):
        str_link = APPDEFAULTS['server']['server_url'] + 'deployment/' + str(dep_id) + '/data?start=' + start + '&end=' + end + \
                   '&simplify=false'
        req = urllib2.Request(str_link)
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def get_sensor_data(self, dep_id, sensor_id):
        str_link = APPDEFAULTS['server']['server_url'] + 'deployment/' + str(dep_id) + '/data?sensors=' + str(sensor_id) + '&simplify=false'
        req = urllib2.Request(str_link)
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def get_sensor_data_within_range(self, depid, sid, start, end):
        str_link = APPDEFAULTS['server']['server_url'] + 'deployment/' + str(depid) + '/data?sensors=' + str(
            sid) + '&start=' + start + '&end=' + end + '&simplify=false'
        req = urllib2.Request(str_link)
        req.add_header('Authorization', 'Token ' + Token.objects.first().key)
        resp = urllib2.urlopen(req)
        content = resp.read()
        return json.loads(content)

    @classmethod
    def pretty_print_jason(strjason):
        output = json.dumps(strjason, indent=2)
        line_list = output.split("\n")  # Sort of line replacing "\n" with a new line
        print('=====================================================================')
        for line in line_list:
            print(line)
        print('=====================================================================')

    @classmethod
    def pretty_write_jason(fname, strjason):
        text_file = open(fname, "w")
        output = json.dumps(strjason, indent=2)
        line_list = output.split("\n")  # Sort of line replacing "\n" with a new line
        for dep_data_jason in line_list:
            text_file.write(str(dep_data_jason))

        text_file.close()


class Room:
    def __init__(self, room_jason):
        self.external_location_list = ['Balcony', 'balcony', 'External', 'external']
        if float(room_jason['room_area']) == 0.0 or None:
            self.room_area = APPDEFAULTS['room_defaults']['room_area']
        else:
            self.room_area = float(room_jason['room_area'])

        if float(room_jason['room_height']) == 0.0 or None:
            self.room_height = APPDEFAULTS['room_defaults']['room_height']
        else:
            self.room_height = float(room_jason['room_height'])

        self.nearest_thermostat = room_jason['nearest_thermostat']
        self.cost = room_jason['cost']
        self.location = room_jason['location']
        self.id = room_jason['sensor']['id']
        self.room_volume = self.room_area * self.room_height

        self.room_mass_air = self.room_volume * APPDEFAULTS['global']['p_air'] # p_air = density of air i.e 1.2kg/m^3
        self.is_energy = 0
        self.is_external = 0
        for channel in room_jason['sensor']['channels']:
            if channel['id'] == 'ELEC':
                self.is_energy = 1
            elif self.location in self.external_location_list or self.id == \
                    APPDEFAULTS['global']['external_temp_sensor_id']:
                self.is_external = 1
            elif channel['id'] not in ['BATT', 'RSSI', 'HUMI']:
                self.is_external = 0
                self.is_energy = 0

        self.data = []
        self.delta_change = []
        self.heating_on_times = []
        self.has_data=False

    def add_data(self, data_jason):
        for sensor in data_jason['sensors']:
            for channel in sensor['channels']:
                vals = []
                times = []
                if channel['id'] not in ['BATT', 'RSSI', 'HUMI']:
                    for point in channel['data']:
                        vals.append(point['value'])
                        times.append(point['time'])

                    times = [datetime.utcfromtimestamp(timestamp / 1000) for timestamp in times]

                    self.data = pd.DataFrame(vals, index=times)
                    self.has_data=True

    def check_re_sample_data_and_compute_room_heating_on_time(self, start, end, set_point_t):
        delta_temp = APPDEFAULTS['global']['delta_temp']
        if self.has_data:
            if self.is_energy == 0:
                self.data = self.data.resample('1T').mean()
                self.data = self.data.interpolate()
                self.data = self.data.fillna(method='ffill')
                values = self.data.values
                n = len(values)
                # make sure we have 1440 datapoints e.g. if after interpolation we still have <1440 points
                # this means some data is missing at the start or end
                if n != 1440:
                    index = pd.date_range(start, end, freq="1T")
                    self.data = self.data.reindex(index)
                    self.data = self.data.interpolate()
                    self.data = self.data.fillna(method='bfill')
                    self.data = self.data.drop(self.data.index[len(self.data) - 1])

                if self.is_external == 0:
                    self.delta_change = np.subtract(values[1:n], values[0:n - 1]).tolist()
                    self.delta_change.append(self.delta_change[-1])

                    self.heating_on_times = np.zeros(n).tolist()
                    prev_one_time = 1
                    for i in range(n):
                        v = values[i]
                        d_t = self.delta_change[i]
                        if v < set_point_t[i] - delta_temp and d_t > 0:
                            self.heating_on_times[i] = 1
                        elif v > set_point_t[i]:
                            self.heating_on_times[i] = 0
                        else:
                            self.heating_on_times[i] = prev_one_time
                        prev_one_time = self.heating_on_times[i]


class Deployment:
    def __init__(self, dep_jason, start, end):
        self.id = int(dep_jason['id'])
        self.times = pd.date_range(start, end, freq='1T')
        self.times = self.times[0:len(self.times) - 1]
        self.default_values_used=False
        self.default_value_fields = []
        # Avg area of 3 bed house = 92.05 sq m as of 2010 survey.
        # http://webarchive.nationalarchives.gov.uk/20110118111538/http://www.cabe.org.uk/files/dwelling-size-survey.pdf
        if float(dep_jason['building_area']) == 0.0 or None:
            self.building_area = APPDEFAULTS['house_defaults']['building_area']
            self.default_values_used=True
            self.default_value_fields.append('building_area')
        else:
            self.building_area = float(dep_jason['building_area'])

        # default building height is 2.4m X 2 = 4.8m i.e two floors.
        if float(dep_jason['building_height']) == 0.0 or None:
            self.building_height = APPDEFAULTS['house_defaults']['building_height']
            self.default_values_used = True
            self.default_value_fields.append('building_height')
        else:
            self.building_height = float(dep_jason['building_height'])

        self.m_air = self.building_area * self.building_height * 1.2
        # default boiler output for a 3 bed house is assumed to be 26kW with a 90% efficiency and default
        # assumption of a gas boiler
        if dep_jason['boiler_output'] is None or '':
            self.boiler_output = APPDEFAULTS['house_defaults']['boiler_output']
            self.default_values_used = True
            self.default_value_fields.append('boiler_output')
        else:
            self.boiler_output = float(dep_jason['boiler_output'])
        self.boiler_output=self.boiler_output*1000 #kw to w

        if dep_jason['boiler_efficiency'] is None or '':
            self.boiler_efficiency = APPDEFAULTS['house_defaults']['boiler_efficiency']
            self.default_values_used = True
            self.default_value_fields.append('boiler_efficiency')
        else:
            self.boiler_efficiency = float(dep_jason['boiler_efficiency'])

        self.boiler_actual_power=self.boiler_output*self.boiler_efficiency

        if dep_jason['boiler_type'] is None or '':
            self.boiler_type = APPDEFAULTS['house_defaults']['boiler_type']
            self.default_values_used = True
            self.default_value_fields.append('boiler_type')
        else:
            if dep_jason['boiler_type'] == 'Gas':
                self.boiler_type = 1
            else:
                self.boiler_type = 0

        # default set point temp is assumed to be 20
        thermo_jason=dep_jason['thermostats']
        #
        n=len(self.times)
        self.boiler_thermostat = [APPDEFAULTS['house_defaults']['boiler_thermostat']] * n
        if thermo_jason is None or '':
            self.default_values_used = True
            self.default_value_fields.append('thermostats')
        else:
            if len(thermo_jason) == 1:
                s1 = float(thermo_jason[0]['setting'])
                if s1 > 0:
                    self.boiler_thermostat = [s1] * n
                else:
                    self.default_values_used = True
                    self.default_value_fields.append('thermostats')

            elif len(thermo_jason) == 2:
                s1 = float(thermo_jason[0]['setting'])
                t1 = thermo_jason[0]['time']
                s2 = float(thermo_jason[1]['setting'])
                t2 = thermo_jason[1]['time']

                if s1 > 0 and s2 > 0:
                    [h1, m1] = t1.split(':')
                    [h2, m2] = t2.split(':')
                    indx1 = int(h1) * 60 + int(m1)
                    indx2 = int(h2) * 60 + int(m2)
                    if indx1 == 0:  # setting start time at 00:00
                        indx1 = n - 1
                    if indx2 == 0:  # setting start time at 00:00
                        indx2 = n - 1

                    if indx2 > indx1:
                        self.boiler_thermostat[indx1:indx2] = [s1] * (indx2 - indx1)
                        self.boiler_thermostat[indx2:n] = [s2] * (n - indx2)
                        self.boiler_thermostat[0:indx1] = [s2] * indx1
                    elif indx1 > indx2:
                        self.boiler_thermostat[indx2:indx1] = [s2] * (indx1 - indx2)
                        self.boiler_thermostat[indx1:n] = [s1] * (n - indx1)
                        self.boiler_thermostat[0:indx2] = [s1] * indx1
                    else:
                        self.boiler_thermostat = [s1] * n
                elif s1 > 0 and s2 <= 0:
                    self.boiler_thermostat = [s1] * n
                elif s1 <= 0 and s2 >= 0:
                    self.boiler_thermostat = [s2] * n
                else:
                    self.default_values_used = True
                    self.default_value_fields.append('thermostats')

        self.note = ""
        self.has_data = False
        self.boiler_manufacturer = dep_jason['boiler_manufacturer']
        self.boiler_model = dep_jason['boiler_model']
        self.hub = dep_jason['hub']
        self.rooms = [Room(room_jason) for room_jason in dep_jason['sensors']]

        if self.default_values_used:
            self.note = APPDEFAULTS['house_defaults']['default_value_warning']

        # additional computed params
        self.web = False
        self.house_internal_temp = []
        self.house_external_temp = []
        self.heating_on_times = []

    def check_deployment_has_temperature_data(self):
        for room in self.rooms: # check if internal temp data is available for at least one room
            if room.is_external == 0 and room.is_energy == 0:
                if room.has_data:
                    self.has_data = True

        for room in self.rooms: # check if external temp data is available
            if room.is_external == 1 and self.has_data:
                if room.has_data:
                    self.has_data = True
                    self.house_external_temp=room.data.values.flatten().tolist()
                else:
                    self.has_data = False


class WhatIf:
    def __init__(self, setPoint, externalTemp):
        self.Set_Point = setPoint
        self.Change_In_External_Temperature = externalTemp


class WhatIfPrediction:
    def __init__(self, hourlyCost, whatIf):
        self.Hourly_Cost_Prediction = hourlyCost
        self.What_If_Conditions = whatIf


class DeploymentPredictions:
    def __init__(self, id, HourlyPredictions, note,default_value_fields):
        self.Deployment_Id = id
        self.What_If_Predictions = HourlyPredictions
        self.Warning = note
        self.Default_Value_Fields= default_value_fields


class DeploymentError:
    def __init__(self, id, errMsg):
        self.Deployment_Id = id
        self.Error = errMsg

import time
import jsonpickle
import codecs, json
import time
from threading import Thread
from chariotanalytics.analytics.ThermalModels import *
from django.http import HttpResponse


def postpone(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@postpone
def post_task():
    all_dep_jason = DataLoader.get_all_deployments()
    ts = time.time()
    start = (datetime.fromtimestamp(ts).replace(hour=0, minute=0, second=0))
    end_dt = start - timedelta(days=1)
    start_dt = start - timedelta(days=2)
    start_dt = start_dt.replace(microsecond=0)
    end_dt = end_dt.replace(microsecond=0)
    start = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    end = end_dt.strftime('%Y-%m-%d %H:%M:%S')
    all_deps = [Deployment(dep_jason, start, end) for dep_jason in all_dep_jason]
    all_dep_predictions = []
    for dep in all_deps:
        for room in dep.rooms:
            room.add_data(DataLoader.get_sensor_data_within_range(dep.id, room.id, start, end))
            room.check_re_sample_data_and_compute_room_heating_on_time(start_dt, end_dt, dep.boiler_thermostat)

        dep.check_deployment_has_temperature_data()
        if dep.has_data:
            thermal_model = APPDEFAULTS['thermal_model']['default_model']
            delta_ext_temps = APPDEFAULTS['what_if_conditions']['delta_ext_temps']
            delta_set_point_temps = APPDEFAULTS['what_if_conditions']['delta_set_point_temps']
            if thermal_model == 'box_thermal_model':
                tm = BoxThermalModel(dep)
            else:
                tm = MultiRoomThermalModel(dep)

            tm.compute_heating_on_times()
            l_rate = tm.learn_leakage_profile()
            # print ('dep = ' + str(dep.id) + ' | leakage rate = ' + str(l_rate))
            all_hourly_predictions = []
            for delta_temp in delta_ext_temps:
                for delta_set_point in delta_set_point_temps:
                    new_set_point = [x + delta_set_point for x in
                                     dep.boiler_thermostat]  # dep.boiler_thermostat + delta_set_point
                    hourly_cost = tm.predict_hourly_cost(delta_temp, new_set_point)
                    wif = WhatIf(new_set_point[0], delta_temp)
                    # wif = WhatIf(delta_set_point, delta_temp)
                    all_hourly_predictions.append(WhatIfPrediction(hourly_cost.tolist(), wif))
            all_dep_predictions.append(
                DeploymentPredictions(dep.id, all_hourly_predictions, dep.note, dep.default_value_fields))
            output = jsonpickle.encode(
                DeploymentPredictions(dep.id, all_hourly_predictions, dep.note, dep.default_value_fields),
                unpicklable=False)

        else:
            all_dep_predictions.append(
                DeploymentError(dep.id, "No Data available for previous day i.e last 24 hours."))
            output = jsonpickle.encode(
                DeploymentError(dep.id, "No Data available for previous day i.e last 24 hours."),
                unpicklable=False)

        DataLoader.post_deployment(dep.id, output)

    output = jsonpickle.encode(all_dep_predictions, unpicklable=False)
    # with codecs.open('data.json', 'w', 'utf8') as f:
    #     f.write(json.dumps(output, sort_keys=True, ensure_ascii=False))

    return output
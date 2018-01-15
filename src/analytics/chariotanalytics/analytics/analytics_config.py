APPDEFAULTS= {
    'server' : {
        'token' : 'Token 4c41700377fd0894b85c8943f5874cbf43c3ac34',
        'server_url' : 'http://web/api/'
    },
    'global': {
      'c_air': 1000,
      'delta_temp': 1,
      'delta_t': 60,
      'electricity_rate': 0.12,
      'gas_rate': 0.032,
      'p_air': 1.2,
      'external_temp_sensor_id': 23
    },
    'what_if_conditions': {
        'delta_ext_temps': [-2, -1, 0, 1, 2],
        'delta_set_point_temps': [-2, -1, 0, 1, 2]
    },
    'thermal_model': {
      'default_model': 'box_thermal_model',
      'box_thermal_model': {
        'assumed_noise': 0.2,
        'max_leakage_rate': 600,
        'leakage_rate_samples': 200
      },
      'multi_room_thermal_model': {
        'smoothing_win': 30,
        'cut_off_percentage': 0.3
      }
    },
    'house_defaults': {
      'building_area': 92.5,
      'building_height': 4.8,
      'boiler_output': 26,
      'boiler_efficiency': 0.9,
      'boiler_type': 1,
      'boiler_thermostat': 20,
      'default_value_warning': 'Warning!! Current predictions are based on default values and may not be accurate. For more accurate predictions please provide values for all fields.',
    },
    'room_defaults': {
      'room_area': 3.2,
      'room_height': 2.4
    },
    'heating_on_time_detection': {
      'default_algo': 'set_point',
      'set_point': {
        'smoothing_win': 10,
        'temp_diff_thresh': 0.004
      },
      'temp_only': {
        'smoothing_win': 10,
        'first_pass_win': 10,
        'first_temp_thresh': 0.2,
        'second_pass_win': 10,
        'second_pass_thresh': 0.5,
        'third_pass_win': 5,
        'third_pass_thresh': 0.8
      }
    }
  }
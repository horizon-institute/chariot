from chariotanalytics.analytics.models import *


class BoxThermalModel:
    def __init__(self, dep):
        self.dep = dep
        self.l_rate = 0
        self.delta_temp = APPDEFAULTS['global']['delta_temp']
        self.delta_t = APPDEFAULTS['global']['delta_t']
        self.assumed_noise = APPDEFAULTS['thermal_model']['box_thermal_model']['assumed_noise']
        self.c_air = APPDEFAULTS['global']['c_air']
        self.e_rate = APPDEFAULTS['global']['electricity_rate']
        self.g_rate = APPDEFAULTS['global']['gas_rate']
        self.is_gas = dep.boiler_type
        self.max_leakage_rate = APPDEFAULTS['thermal_model']['box_thermal_model']['max_leakage_rate']
        self.leakage_rate_samples = APPDEFAULTS['thermal_model']['box_thermal_model']['leakage_rate_samples']

    def learn_leakage_profile(self):
        leak_rates = np.linspace(0, self.max_leakage_rate, self.leakage_rate_samples)
        n = len(self.dep.times)
        best_mse = 999999
        best_l_rate = 0
        for l_rate in leak_rates:
            t_int_est, _, _, _, _ = \
                self.predict_internal_temp(self.dep.boiler_actual_power, self.dep.house_internal_temp[0],
                                           self.dep.house_external_temp, self.dep.boiler_thermostat,
                                           l_rate, self.dep.m_air, self.delta_temp, self.delta_t,
                                           self.c_air, self.assumed_noise)

            current_mse = Util.compute_mse(t_int_est, self.dep.house_internal_temp)
            if current_mse < best_mse:
                best_mse = current_mse
                best_l_rate = l_rate

        self.l_rate = best_l_rate

        return best_l_rate

    def is_the_heater_on(self, indx, int_t, set_t, pre_heater_state, delta_temp):
        is_heater_on_or_off = 0
        # if self.dep.heating_on_times[indx] == 1:
        if int_t > set_t + delta_temp:
            is_heater_on_or_off = 0
        elif int_t < set_t - delta_temp:
            is_heater_on_or_off = 1
        else:
            is_heater_on_or_off = pre_heater_state
        return is_heater_on_or_off

    def predict_internal_temp(self, h_output, start_temp, ext_temp, set_point_temp,
                              l_rate, m_air, delta_temp, delta_t, c_air, assumed_noise):
        n = len(ext_temp)
        t_int_est = [0.] * n
        energy_loss_or_gain = [0.] * n
        t_int_est[0] = start_temp
        energy_loss_or_gain[0] = 0
        heater_on_profile = np.zeros(n)
        for i in xrange(n - 1):
            heater_on_profile[i] = self.is_the_heater_on(i, t_int_est[i], set_point_temp[i],
                                                         heater_on_profile[i - 1], delta_temp)
            energy_loss_or_gain[i] = heater_on_profile[i] * h_output - \
                                     l_rate * (t_int_est[i] - ext_temp[i]) + assumed_noise
            t_int_est[i + 1] = t_int_est[i] + (energy_loss_or_gain[i] * delta_t) / (c_air * m_air)

        cost_rate = self.e_rate
        if self.is_gas == 1:
            cost_rate = self.g_rate

        hours_heater_was_on = (np.count_nonzero(heater_on_profile) * 1) / 60
        heating_cost = (hours_heater_was_on * (h_output / 1000)) * cost_rate

        heating_profile_hourly = np.mean(heater_on_profile.reshape(-1, 60), axis=1)
        heating_hourly_cost = heating_profile_hourly * (h_output / 1000) * cost_rate

        heating_kwh_hourly = heating_profile_hourly * (h_output / 1000)
        return t_int_est, heater_on_profile.tolist(), heating_cost, heating_hourly_cost, heating_kwh_hourly

    def predict_hourly_cost(self, delta_ext_temp, new_set_point, show_plots=False):
        new_ext_temp = [x + delta_ext_temp for x in self.dep.house_external_temp]
        t_int_est, heater_profile, heating_cost, heating_hourly_cost, heating_profile_hourly = \
            self.predict_internal_temp(self.dep.boiler_actual_power, self.dep.house_internal_temp[0],
                                       new_ext_temp, new_set_point, self.l_rate, self.dep.m_air,
                                       self.delta_temp, self.delta_t, self.c_air, self.assumed_noise)
        # if show_plots:
        #     plt.figure()
        #     ax1=plt.subplot(3, 1, 1)
        #     plt.plot(heater_profile,label='Heater On Profile')
        #     ax1.legend(loc='upper center', shadow=True)
        #     plt.title('Detla T = '+str(delta_ext_temp)+' | Set Point T = '+str(new_set_point) +
        #               ' | Daily Cost = '+str(np.sum(heating_hourly_cost)))
        #     ax2 =plt.subplot(3, 1, 2)
        #     plt.plot(t_int_est,label='Internal')
        #     plt.plot(new_ext_temp,label='External')
        #     plt.plot([new_set_point + self.delta_temp] * len(heater_profile),'k--')
        #     plt.plot([new_set_point] * len(heater_profile),label='Set Point')
        #     plt.plot([new_set_point - self.delta_temp] * len(heater_profile),'k--')
        #     ax2.legend(loc='upper center', shadow=True)
        #     ax3 =plt.subplot(3, 1, 3)
        #     plt.plot(heating_hourly_cost,label='Hourly Cost')
        #     ax3.legend(loc='upper center', shadow=True)
        #     plt.draw()
        return heating_hourly_cost

    def compute_heating_on_times(self):
        algo = APPDEFAULTS['heating_on_time_detection']['default_algo']
        n = len(self.dep.times)
        monitored_room_counter = 0
        self.dep.found_thermostat_temp = False
        self.dep.house_internal_temp = np.zeros(n)
        self.dep.heating_on_times = np.zeros(n)

        # find room where the thermostat is located or take average of all rooms
        for r in self.dep.rooms:
            if r.is_external == 0 and r.is_energy == 0:
                monitored_room_counter = monitored_room_counter + 1
                self.dep.house_internal_temp = self.dep.house_internal_temp + r.data.values.flatten()
                #                 print (self.dep.house_internal_temp.flatten())
                if r.nearest_thermostat is True:
                    self.dep.found_thermostat_temp = True
                    self.dep.house_internal_temp = np.array(r.data.values.tolist())
                    break

        if not self.dep.found_thermostat_temp:
            self.dep.house_internal_temp = [x / monitored_room_counter for x in self.dep.house_internal_temp]

        if algo is 'set_point':
            # detect heating times based on set-point temperature and actual internal and external temp
            # see description at http://185.157.234.235:8080/sim_desc
            smoothing_win = APPDEFAULTS['heating_on_time_detection']['set_point']['smoothing_win']
            temp_diff_thresh = APPDEFAULTS['heating_on_time_detection']['set_point']['temp_diff_thresh']
            # smooth temp data with a moving avg window of 10 mins
            self.dep.house_internal_temp = Util.smooth(self.dep.house_internal_temp, smoothing_win)
            self.dep.house_external_temp = Util.smooth(self.dep.house_external_temp, smoothing_win)

            prev_heating_state = 0
            for i in range(n):
                c_temp = self.dep.house_internal_temp[i]
                temp_diff = 0
                temp_diff_ext = 0
                if i < n - 1:
                    temp_diff = self.dep.house_internal_temp[i + 1] - c_temp
                    temp_diff_ext = self.dep.house_external_temp[i + 1] - self.dep.house_external_temp[i]

                if c_temp > self.dep.boiler_thermostat[i] + self.delta_temp:
                    self.dep.heating_on_times[i] = 0
                elif c_temp < self.dep.boiler_thermostat[i] - self.delta_temp:
                    if temp_diff > temp_diff_thresh and temp_diff > temp_diff_ext:
                        self.dep.heating_on_times[i] = 1
                    else:
                        self.dep.heating_on_times[i] = 0
                else:
                    self.dep.heating_on_times[i] = prev_heating_state
                prev_heating_state = self.dep.heating_on_times[i]

        elif algo is 'temp_only':  # detect heating times based on internal temperature change only
            smoothing_win = APPDEFAULTS['heating_on_time_detection']['temp_only']['smoothing_win']
            first_pass_win = APPDEFAULTS['heating_on_time_detection']['temp_only']['first_pass_win']
            first_temp_thresh = APPDEFAULTS['heating_on_time_detection']['temp_only']['first_temp_thresh']
            second_pass_win = APPDEFAULTS['heating_on_time_detection']['temp_only']['second_pass_win']
            second_pass_thresh = APPDEFAULTS['heating_on_time_detection']['temp_only']['second_pass_thresh']
            third_pass_win = APPDEFAULTS['heating_on_time_detection']['temp_only']['third_pass_win']
            third_pass_thresh = APPDEFAULTS['heating_on_time_detection']['temp_only']['third_pass_thresh']

            # First Pass:
            # Select consecutive readings 15 min apart, if the difference between the later and
            # the former is greater than 0.2 C and also greater than chane in external temp, assume heating is on
            for i in range(n):
                ed = i + first_pass_win
                if ed >= n - first_pass_win:
                    ed = n - 1
                v1 = self.dep.house_internal_temp[i]
                ve = self.dep.house_internal_temp[ed]
                i_diff = np.array(ve) - np.array(v1)
                e1 = self.dep.house_external_temp[i]
                e2 = self.dep.house_external_temp[ed]
                e_diff = np.array(e1) - np.array(e2)

                if i_diff > first_temp_thresh and i_diff > e_diff:
                    self.dep.heating_on_times[i] = 1
                else:
                    self.dep.heating_on_times[i] = 0

            # Second Pass:
            # From the detected heating on times (First pass), if 50% of the readings in a consecutive 10 min interval
            # are heating on then select that time-slot as heating on other wise set it as heating off
            for i in range(n):
                ed = i + second_pass_win
                if ed >= n - second_pass_win:
                    ed = n - 1
                vals_gt_zero = sum(v > 0 for v in self.dep.heating_on_times[i:ed])
                if vals_gt_zero > second_pass_win * second_pass_thresh:
                    self.dep.heating_on_times[i] = 1
                else:
                    self.dep.heating_on_times[i] = 0

            # Third Pass:
            # From the detected heating on times (Second pass), if 80% of the readings in a consecutive 5 min interval
            # are heating on then select that time-slot as heating on other wise set it as heating off
            for i in range(n):
                ed = i + third_pass_win
                if ed >= n - third_pass_win:
                    ed = n - 1
                vals_gt_zero = sum(v > 0 for v in self.dep.heating_on_times[i:ed])
                if vals_gt_zero > third_pass_win * third_pass_thresh:
                    self.dep.heating_on_times[i] = 1
                else:
                    self.dep.heating_on_times[i] = 0


class MultiRoomThermalModel:
    def __init__(self, dep):
        self.dep = dep

    def learn_leakage_profile(self):
        status = "Not Implemented"

    def compute_heating_on_times(self):
        status = "Not Implemented"

    def predict_internal_temp(self):
        status = "Not Implemented"

    def predict_hourly_cost(self, delta_ext_temp, new_set_point, show_plots=False):
        status = "Not Implemented"

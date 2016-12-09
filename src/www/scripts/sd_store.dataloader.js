var sd_store;
if (!sd_store) {
	sd_store = {};
}

sd_store.dataloader = (function () {
	'use strict';
	var parse_reading = function (o) {
		return {'value': o.value, 't': moment(o.t).toDate()};
	};

	var parse_annotation = function (o) {
		o.start = moment(o.start).toDate();
		o.end = moment(o.end).toDate();
		return o;
	};

	var format_date = function (date) {
		return moment(date).format('YYYY-MM-DD HH:mm:ss');
	};

	var load_everything = function (p, on_data_loaded) {
		var chained_load_readings,
			request_info = [],
			load_readings,
			on_everything_loaded;

		on_everything_loaded = function () {
			var parsed_data = [];
			var checked_arguments;
			// we need to check whether we got more than one group of arguments
			if (arguments.length === 3 && arguments[2].hasOwnProperty('statusText') === true) {
				// this means there is only one group of readings
				checked_arguments = [arguments];
			} else {
				checked_arguments = arguments;
			}

			for (var i = 0; i < checked_arguments.length; i += 1) {
				var curr = checked_arguments[i][0];
				if (curr.hasOwnProperty('data')) {
					curr.sensor = request_info[i].sensor;
					curr.channel = request_info[i].channel;
					curr.readings = curr.data.map(parse_reading);
					curr.query = request_info[i].query;

					if (p.annotations === true && curr.hasOwnProperty('annotations') === true) {
						curr.annotations = curr.annotations.map(parse_annotation);
					}

					parsed_data.push(curr);
				}
			}

			on_data_loaded(parsed_data);
		};

		load_readings = function (sensors) {
			var requests = [];
			var url_data = {
				start: format_date(p.start),
				end: format_date(p.end)
			};

			for (var sensor_index = 0; sensor_index < sensors.length; sensor_index += 1) {
				var sensor = sensors[sensor_index];
				for (var channel_index = 0; channel_index < sensor.channels.length; channel_index += 1) {
					var channel = sensor.channels[channel_index];
					if(channel.stats.value__avg != null) {
						var curr_url = p.url + p.deployment + "/data/" + sensor.id + "/" + channel.name;
						var query = 'data';
						requests.push($.ajax({
							url: curr_url,
							data: url_data
						}).promise());
						request_info.push({
							sensor: sensor,
							channel: channel,
							query: query
						});
					}
				}
			}

			// based on http://stackoverflow.com/questions/5627284/pass-in-an-array-of-deferreds-to-when
			return $.when.apply(null, requests);
		};

		chained_load_readings = load_readings(p.sensors);
		chained_load_readings.done(on_everything_loaded);
	};

	// export the API
	return {
		load: load_everything
	};
}());

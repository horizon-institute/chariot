var fe;
if (!fe) {
	fe = {};
}


$(function () {
	'use strict';
	if (!fe) {
		fe = {};
	}
	if (!fe.logger) {
		fe.logger = {};
	}

	fe.datastore = (function () {
		var raw_data = null;
		var data_sets = [];
		var annotations = {};

		var x_min = -1;
		var x_max = -1;
		var colours = [
			"#c76434",
			"#6971d7",
			"#acb839",
			"#563889",
			"#64c673",
			"#923076",
			"#83aa3e",
			"#cc79cd",
			"#5e8e3e",
			"#d96699",
			"#45c097",
			"#da585c",
			"#6d8dd7",
			"#d1972c",
			"#ae3d5d",
			"#c3a64e",
			"#9a3f2f",
			"#9c7835"
		];

		var clear = function () {
			data_sets = [];
			annotations = {};
		};

		var add_annotation = function (annotation) {
			annotation.start = moment(annotation.start);
			annotation.end = moment(annotation.end);
			annotations[annotation.id] = annotation;
			raw_data.annotations.push(annotation);
		};

		var remove_annotation = function (annotation) {
			for(var index = 0; index < raw_data.annotations.length; index ++) {
				if(raw_data.annotations[index].id == annotation.id) {
					raw_data.annotations.splice(index, 1);
					break;
				}
			}
			delete annotations[annotation.id];
		};

		var data_point = function(channel, time, value) {
			if('y_max' in channel) {
				channel.y_max = Math.max(channel.y_max, value);
			} else {
				channel.y_max = value;
			}
			if('y_min' in channel) {
				channel.y_min = Math.min(channel.y_min, value);
			} else {
				channel.y_min = value;
			}

			return {
				time: time,
				value: value
			}
		};

		var get_position = function(point1, point2, time) {
			return ((time - point1.time) / (point2.time - point1.time)) * (point2.value - point1.value) + point1.value;
		};

		var filter_data = function(start, end) {
			clear();
			var filteredData = jQuery.extend(true, {}, raw_data);
			$.each(filteredData.sensors, function (index, sensor) {
				$.each(sensor.channels, function (index, channel) {
					var prev = null;
					var filtered = [];
					$.each(channel.data, function (index, dataItem) {
						if(dataItem.time.isAfter(start)) {
							if(dataItem.time.isBefore(end)) {
								if(prev && prev.time.isBefore(start)) {
									filtered.push(data_point(channel, start, get_position(prev, dataItem, start)));
								}
								filtered.push(data_point(channel, dataItem.time, dataItem.value));
							} else {
								if(prev && prev.time.isBefore(end)) {
									if(prev.time.isBefore(start)) {
										filtered.push(data_point(channel, start, get_position(prev, dataItem, start)));
									}
									filtered.push(data_point(channel, end, get_position(prev, dataItem, end)));
								} else {
									return false;
								}
							}
						}
						prev = dataItem;

					});

					channel.data = filtered;
					if(channel.data.length > 0) {
						channel.x_max = channel.data[channel.data.length - 1].time;
						channel.x_min = channel.data[0].time;
						channel.channel = channel.id;
						channel.sensor = sensor.id;

						channel.colour = colours[data_sets.length];
						channel.selected = false;
						channel.visible = true;

						var h = fe.logger.plot.get_height();
						var w = fe.logger.plot.get_width();
						channel.ySc = d3.scale.linear().domain([0, 1.1 * channel.y_max]).range([0, h]);
						channel.xSc = d3.time.scale().domain([channel.x_min, channel.x_max]).range([0, w]);

						add_dataset(channel);
					}
				});
			});
			filteredData.annotations = filteredData.annotations.filter(function (value) {
				return value.start.isBetween(start, end) || value.end.isBetween(start, end);
			});

			$.each(filteredData.annotations, function (index, annotation) {
				annotations[annotation.id] = annotation;
			});

			return filteredData;
		};

		var add_dataset = function (dataset) {
			data_sets.push(dataset);

			$.each(fe.datastore.get_datasets(), function (index, dataset) {
				if (x_min == -1 || dataset.x_min < x_min) {
					x_min = dataset.x_min;
				}
				if (x_max == -1 || dataset.x_max > x_max) {
					x_max = dataset.x_max;
				}
			});
		};

		var lookup = function (sensor_id, channel_id) {
			var found = null;
			$.each(data_sets, function (index, dataset) {
				if (dataset.channel == channel_id && dataset.sensor == sensor_id) {
					found = dataset;
				}
			});
			return found;
		};

		var lookup_channel = function (channel_id) {
			var found = null;
			$.each(data_sets, function (index, dataset) {
				if (dataset.channel == channel_id) {
					found = dataset;
				}
			});
			return found;
		};

		var load = function (start, end, callback) {
			if(raw_data == null) {
				$.getJSON(DATA_URL, function (data) {
					$.each(data.sensors, function (index, sensor) {
						$.each(sensor.channels, function (index, channel) {
							$.each(channel.data, function (index, dataItem) {
								dataItem.time = moment(dataItem.time);
							});
						});
					});
					$.each(data.annotations, function (index, annotation) {
						annotation.start = moment(annotation.start);
						annotation.end = moment(annotation.end);
					});

					raw_data = data;
					var filteredData = filter_data(start, end);
					fe.logger.plot.redraw();
					if (callback) {
						callback(filteredData);
					}
				});
			}
			else {
				var filteredData = filter_data(start, end);
				fe.logger.plot.redraw();
				if (callback) {
					callback(filteredData);
				}
			}
		};

		var get_datasets = function () {
			return data_sets;
		};

		var get_annotations = function () {
			return annotations;
		};

		// export the API
		return {
			add_annotation: function (annotation) {
				add_annotation(annotation);
			},
			get_datasets: function () {
				return get_datasets();
			},
			get_position: function(point1, point2, time) {
				return get_position(point1, point2, time);
			},
			get_annotations: function () {
				return get_annotations();
			},
			clear: function () {
				clear();
			},
			load: function(start, end, callback) {
				load(start, end, callback);
			},
			remove_annotation: function (annotation) {
				return remove_annotation(annotation);
			},
			lookup: function (sensor_id, channel_id) {
				return lookup(sensor_id, channel_id);
			},
			lookup_channel: function (channel_id) {
				return lookup_channel(channel_id);
			}
		};
	}());
});
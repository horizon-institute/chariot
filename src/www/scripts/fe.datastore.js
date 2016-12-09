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

	function normaliseKernel(a) {
		function arraySum(a) {
			var s = 0;
			for (var i = 0; i < a.length; i++) {
				s += a[i];
			}
			return s;
		}

		var sum_a = arraySum(a);
		var scale_factor = sum_a / 1;
		a = a.map(function (d) {
			return d / scale_factor;
		});
		return a;
	}

	fe.datastore = (function () {
		var data_sets = [];
		var annotations = {};

		var x_min = -1;
		var x_max = -1;

		var clear = function () {
			data_sets = [];
			annotations = {};
		};

		var add_annotation = function (annotation) {
			annotations[annotation.id] = annotation;
			annotations[annotation.id].start = moment(annotation.start);
			annotations[annotation.id].end = moment(annotation.end);
		};

		var remove_annotation = function (annotation) {
			delete annotations[annotation.id];
		};

		var add_dataset = function (dataset, colour) {
			data_sets.push(build_dataset(dataset, colour));

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

		var build_dataset = function (data, colour) {
			var kernel = normaliseKernel([0.1, 0.2, 0.3, 0.2, 0.1]);

			var dataset = {};
			dataset.y_max = Math.max(d3.max(data.readings, function (d) {
				return d.value;
			}), 0);
			dataset.y_max = Math.max(1.0, dataset.y_max);
			dataset.y_min = d3.min(data.readings, function (d) {
				return d.value;
			});
			dataset.x_max = data.readings[data.readings.length - 1].t;
			dataset.x_min = data.readings[0].t;
			dataset.data = data.readings;
			dataset.channel = data.channel.id;
			dataset.sensor = data.sensor.id;
			dataset.units = data.channel.units;

			console.log(data.channel);

			// These properties are more for view purposes.
			dataset.colour = colour;
			dataset.name = data.channel.name;
			// Whether there's a selected portion.
			dataset.selected = false;
			// Whether the dataset is actually visible on the graph.
			dataset.visible = true;


			var h = fe.logger.plot.get_height();
			var w = fe.logger.plot.get_width();
			dataset.ySc = d3.scale.linear().domain([0, 1.1 * dataset.y_max]).range([0, h]);
			dataset.xSc = d3.time.scale().domain([dataset.x_min, dataset.x_max]).range([0, w]);

			return dataset;
		};

		var load = function (data, settings) {
			clear();
			$.each(data.annotations, function (index, annotation) {
				fe.datastore.add_annotation(annotation);
			});

			var pos = 0;
			$.each(data.readings, function (index, datum) {
				if (datum.readings.length > 0) {
					fe.datastore.add_dataset(datum, settings.colours[pos % settings.colours.length]);
				}
				pos++;
			});
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
			add_dataset: function (dataset, colour) {
				add_dataset(dataset, colour);
			},
			get_datasets: function () {
				return get_datasets();
			},
			get_annotations: function () {
				return get_annotations();
			},
			clear: function () {
				clear();
			},
			load: function (data, colours) {
				load(data, colours);
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
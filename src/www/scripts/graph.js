var filtered_channels = [];
var selected_axis_l;
var selected_axis_r;
var startDate;
var endDate;
var zooms = [];


function qs(key) {
	key = key.replace(/[*+?^$.\[\]{}()|\\\/]/g, "\\$&"); // escape RegEx meta chars
	var match = location.search.match(new RegExp("[?&]" + key + "=([^&]+)(&|$)"));
	return match && decodeURIComponent(match[1].replace(/\+/g, " "));
}


$(document).ready(function () {
	var chartDiv = $('#chart');
	chartDiv.logger({
		'all_channels': qs('channels') == 'all'
	});
	chartDiv.bind("logger:click", function (event, params) {
		if (params.button == 'clear_selection') {
			$("#zoomIn").prop("disabled", true);
			$("#addAnnotation").hide();
		}
		else if (params.button == 'create_selection') {
			$("#zoomIn").prop("disabled", false);
			var annotationItem = $('#toggleAnnotations');
			var annotations = annotationItem.data('show');
			if (annotations) {
				$("#addAnnotation").show();
			}
		}
	});

	$('#dateFilter')
		.dateRangePicker({
			autoClose: true,
			format: 'D MMM YYYY',
			separator: ' – ',
			showShortcuts: true,
			startOfWeek: 'monday',
			shortcuts: {
				'prev': ['week', 'month', 'year']
			},
			startDate: moment(dataStart).format('D MMM YYYY'),
			endDate: moment(dataEnd).format('D MMM YYYY')
		})
		.bind('datepicker-change', function (event, obj) {
			var startDay = moment(obj.date1).startOf('day');
			var endDay = moment(obj.date2).endOf('day');
			var dataStartDay = moment(dataStart).startOf('day');
			var dataEndDay = moment(dataEnd).endOf('day');
			if (!startDay.isSame(dataStartDay) || !endDay.isSame(dataEndDay)) {
				zooms = [{
					startDate: dataStartDay,
					endDate: dataEndDay
				}];
				$("#zoomOut").prop("disabled", false);
			}
			else {
				zooms = [];
				$("#zoomOut").prop("disabled", true);
			}
			update_date_range(startDay, endDay);
		});

	$('#addAnnotation')
		.hide()
		.click(function (event) {
			var plot = fe.logger.plot;
			var selection = plot.get_selection();
			if (selection.w > 0) {
				var selection_start_t = plot.get_time_for_x(selection.x);
				var selection_end_t = plot.get_time_for_x(selection.x + selection.w);
				var selected_layer = fe.logger.annotation.get_selected_layer();
				if (selected_layer) {
					show_annotation_editor({
						"id": null,
						"text": "",
						"start": selection_start_t,
						"end": selection_end_t,
						"layer": selected_layer.ref
					});

					event.stopPropagation();
				}
			}
		});
	$('#toggleAnnotations')
		.hide()
		.data('show', true)
		.click(function () {
			var annotationItem = $('#toggleAnnotations');
			var annotations = annotationItem.data('show');
			if (annotations) {
				$(".carpet").hide();
				$(".graph-annotation").hide();
				$('#addAnnotation').hide();
				annotationItem
					.data('show', false)
					.children('.material-icons')
					.attr('style', "color: #AAA")
					.text('visibility_off');

			} else {
				fe.logger.plot.clear_selection();
				$(".carpet").show();
				$(".graph-annotation").show();
				annotationItem
					.data('show', true)
					.children('.material-icons')
					.removeAttr('style')
					.text('visibility');
			}
		});

	$("#zoomIn").click(function () {
		var selection = fe.logger.plot.get_selection();
		if (selection.w > 0) {
			zooms.push({
				startDate: startDate,
				endDate: endDate
			});
			$("#zoomOut").prop("disabled", false);
			update_date_range(moment(fe.logger.plot.get_time_for_x(selection.x)), moment(fe.logger.plot.get_time_for_x(selection.x + selection.w)));
			fe.logger.plot.clear_selection();
		}
	}).prop("disabled", true);
	$("#zoomOut").click(function () {
		var zoom = zooms.pop();
		$("#zoomOut").prop("disabled", zooms.length == 0);
		update_date_range(zoom.startDate, zoom.endDate);
	}).prop("disabled", true);

	// If an event gets to the body
	$("#annotations-edit-dialog").click(function () {
		$("#annotations-edit-dialog").fadeOut();
	}).children().click(function (e) {
		e.stopPropagation();
	});

	update_date_range(moment(dataStart).startOf('day'), moment(dataEnd).endOf('day'));
	$(window).resize(function () {
		fe.logger.plot.redraw();
	});
});

var update_date_range = function (start, end) {
	startDate = start;
	endDate = end;

	if (startDate.isSame(endDate, 'day')) {
		$('#dateFilter').text(startDate.format('D MMM YYYY'));
	}
	else if (startDate.year() === endDate.year()) {
		if (startDate.month() === endDate.month()) {
			$('#dateFilter').text(startDate.format('D') + ' – ' + endDate.format('D MMM YYYY'));
		}
		else {
			$('#dateFilter').text(startDate.format('D MMM') + ' – ' + endDate.format('D MMM YYYY'));
		}
	}
	else {
		$('#dateFilter').text(obj.value);
	}

	//$('#load-spinner').fadeIn();
	fe.datastore.load(startDate, endDate, rebuild_view);
};

var rebuild_view = function (data) {
	$('#load-spinner').fadeOut();
	fe.logger.plot.clear_selection();
	build_menu(data.sensors);
	filter_streams();
};

function build_menu(sensors) {
	var visibilityMenu = $('#visibilityMenu');
	visibilityMenu.empty();

	var axisMenu = $('#axisMenu');
	axisMenu.empty();

	$('#toggleAnnotations').show();

	var channels = {};
	$.each(sensors, function (i, device) {
		$.each(device.channels, function (j, channel) {
			if (channel.data.length > 1) {
				channels[channel.id] = channel;
			}
		});
	});

	$.each(channels, function (channelID, channel) {
		if (selected_axis_l == undefined) {
			selected_axis_l = channelID;
		} else if (selected_axis_r == undefined) {
			selected_axis_r = channelID;
		}

		if (Object.keys(channels).length > 1) {
			var elem = $('<div></div>')
				.addClass('axis-item')
				.data('channel-id', channel.id);

			elem.append('<input type="radio" name="axis-left" class="radio">');
			elem.append('<span style="flex: 1">' + channel.name + '</span>');
			elem.append('<input type="radio" name="axis-right" class="radio">');
			axisMenu.append(elem);
		}

		$(".radio").click(function () {
			var radio = $(this);
			var item = radio.parent();
			var channel = item.data('channel-id');
			select_axis_channel(channel, radio[0].name === "axis-left");
		});

		var channelSection = $('<details open></details>');
		channelSection.append('<summary class="mdl-typography--subhead">' + channel.name + '</summary>');

		$.each(sensors, function (i, device) {
			$.each(device.channels, function (j, stream) {
				if (stream.id === channel.id && stream.data.length > 1) {
					var key = "" + device.id + ":" + stream.id;
					var selected = true;
					var filterIcon = 'visibility';

					if (filtered_channels.indexOf(key) != -1) {
						selected = false;
						filterIcon = 'visibility_off';
					}

					var value_min = null;
					var value_max = null;
					var value_avg = 0;
					var avg_duration = 0;
					var previous = null;
					$.each(stream.data, function (i, dataItem) {
						if (value_min == null || dataItem.value < value_min) {
							value_min = dataItem.value;
						}
						if (value_max == null || dataItem.value > value_max) {
							value_max = dataItem.value;
						}

						if (previous != null) {
							var prev_duration = dataItem.time - previous.time;
							var total_duration = prev_duration + avg_duration;

							var avg = (previous.value + dataItem.value) / 2;
							value_avg = ((avg * prev_duration) + (value_avg * avg_duration)) / total_duration;
							avg_duration = total_duration;
						}
						previous = dataItem;
					});

					var content = $('<div></div>')
						.append('<div>' + (device.location || device.name || 'Sensor') + '</div>');
					if (value_min != null && value_max != null) {
						content.append('<div class="mdl-typography--caption-color-contrast">' +
							value_min.toFixed(2) + stream.units + ' – ' +
							value_max.toFixed(2) + stream.units +
							'</div>')
							.append('<div class="mdl-typography--caption-color-contrast">' +
								' Avg: ' + value_avg.toFixed(2) + stream.units +
								'</div>');

						if (device.cost) {
							var cost = value_avg * moment.duration(avg_duration).asHours() * device.cost / 1000;
							if (cost < 100) {
								content.append('<div class="mdl-typography--caption-color-contrast">' +
									' Cost: ' + cost.toFixed(1) + 'p</div>')
							} else {
								cost /= 100;
								content.append('<div class="mdl-typography--caption-color-contrast">' +
									' Cost: £' + cost.toFixed(2) + '</div>')
							}
						}
					}


					var elem = $('<div></div>')
						.addClass('visibility-item')
						.append('<i class="material-icons">' + filterIcon + '</i>')
						.append(content)
						.data('selected', selected)
						.data('channel-id', stream.id)
						.data('sensor-ref', device.id)
						.click(function () {
							var item = $(this);
							var selected = !item.data('selected');
							var new_channel = item.data('channel-id');
							var new_sensor = item.data('sensor-ref');
							var key = "" + new_sensor + ":" + new_channel;

							update_item_visibility(item, selected);
							item.data('selected', selected);

							if (selected) {
								var index = filtered_channels.indexOf(key);
								if (index > -1) {
									filtered_channels.splice(index, 1);
								}
								select_axes(new_channel);
							} else {
								filtered_channels.push(key);
								select_axes(false);
							}
							filter_streams();
						})
						.mouseover(function () {
							var item = $(this);
							var sensor = item.data('sensor-ref');
							highlight_sensor(sensor);
						})
						.mouseout(function () {
							highlight_sensor(null);
						});

					var dataset = fe.datastore.lookup(device.id, stream.id);
					if (dataset) {
						elem.data('color', dataset.colour);
						update_item_visibility(elem, selected);
					}
					channelSection.append(elem);
				}
			});
		});

		visibilityMenu.append(channelSection);
	});

	if (selected_axis_r == undefined) {
		selected_axis_r = selected_axis_l;
	}

	select_axis_channel(selected_axis_l, true);
	select_axis_channel(selected_axis_r, false);
}


function highlight_sensor(sensor) {

}


function select_axes(new_channel) {
	var streams = get_selected_streams();

	var unique_channels = [];
	$.each(streams, function (index, stream) {
		if (unique_channels.indexOf(stream.channel) == -1) {
			unique_channels.push(stream.channel);
		}
	});

	var curr = [selected_axis_l, selected_axis_r];

	if (unique_channels.length == 1) {
		// If only 1 channel is selected, and it's not the left-most,
		// make it the left axis.
		if (selected_axis_l != unique_channels[0]) {
			select_axis_channel(unique_channels[0], true);
			select_axis_channel(unique_channels[0], false);
		}
	}
	else if (unique_channels.length > 1) {
		// If >1 channel is selected, and we've selected a 
		// new channel, make it the right-most.
		if (new_channel && curr.indexOf(new_channel) == -1) {
			select_axis_channel(new_channel, false);
		}
		else {
			// We've removed a channel - if it's currently
			// an axis, then swap for a different one.
			var lhs_pos = unique_channels.indexOf(selected_axis_l);
			var rhs_pos = unique_channels.indexOf(selected_axis_r);
			if (lhs_pos == -1) {
				// Swap the left axis for one that exists.
				unique_channels.splice(rhs_pos, 1);
				select_axis_channel(unique_channels[unique_channels.length - 1], true);
			}
			else if (rhs_pos == -1) {
				// Swap the right axis for one that exists.
				unique_channels.splice(lhs_pos, 1);
				select_axis_channel(unique_channels[unique_channels.length - 1], false);
			}
		}
	}
}

var select_axis_channel = function (key, left) {
	console.log("Select " + (left ? 'left' : 'right') + " channel: " + key);
	var radio_name = left ? "input[name=axis-left]" : "input[name=axis-right]";
	$(".axis-item").each(function () {
		var channel = $(this).data('channel-id');
		if (channel == key) {
			$(this).find(radio_name).attr("checked", true);
		}
		else {
			$(this).find(radio_name).attr("checked", false);
		}
	});

	if (left) {
		selected_axis_l = key;
	}
	else {
		selected_axis_r = key;
	}
	fe.logger.plot.set_axis_channel(key, left);
};


// Show the colour band
function update_item_visibility(elem, visible) {
	if (visible) {
		elem.data('shown', visible)
			.children(".material-icons")
			.attr('style', "color:" + elem.data('color'))
			.text('visibility');
	} else {
		elem.data('shown', visible)
			.children(".material-icons")
			.attr('style', "color: #AAA")
			.text('visibility_off');
	}
}

function get_selected_streams() {
	var selections = $(".visibility-item").filter(function () {
		return $(this).data('selected');
	});
	var streams = [];
	$.each(selections, function (index, selection) {
		var stream = {};
		stream['sensor'] = $(selection).data('sensor-ref');
		stream['channel'] = $(selection).data('channel-id');
		streams.push(stream);
	});
	return streams;
}

function filter_streams() {
	// Update filters
	var selections = $(".visibility-item").filter(function () {
		return $(this).data('selected');
	});

	var channels = [];
	$.each(selections, function (index, selection) {
		var $this = $(selection);
		var filt = {'sensor': $this.data('sensor-ref'), 'channel': $this.data('channel-id')};
		channels.push(filt);
	});
	fe.logger.plot.filter_channels(channels);
}

function show_annotation_editor(annotation) {
	$('#an_layer').val(annotation.layer);
	$('#an_start').val(moment(annotation.start).format('DD/MM/YYYY HH:mm:ss'));
	$('#an_end').val(moment(annotation.end).format('DD/MM/YYYY HH:mm:ss'));
	$('#an_deployment').val(DEPLOYMENT_ID);
	$('#an_annotation').val(annotation.id);
	if (annotation.id) {
		$("#annotation-delete").click(function (event) {
			event.preventDefault();
			event.stopImmediatePropagation();
			var annotation_id = $("#an_annotation").val();
			var data = $("#annotations-edit-dialog").serialize();
			$.post(ANNOTATION_URL + '/' + annotation_id + "/delete", data, function () {
				fe.datastore.remove_annotation({'id': annotation_id});
				fe.logger.plot.redraw();
				$('#annotations-edit-dialog').fadeOut();
			}).fail(function () {
			});
		}).show();
		$('#annotation-save').text('Update');
	}
	else {
		$("#annotation-delete").hide();
		$('#annotation-save').text('Create');
	}

	$("#annotations-edit-dialog").submit(function (event) {
		event.preventDefault();
		event.stopImmediatePropagation();
		console.log('Submitting');
		var url = ANNOTATION_URL;
		var annotation_id = $("#an_annotation").val();
		if (annotation_id !== undefined && annotation_id !== '') {
			url = ANNOTATION_URL + '/' + annotation_id;
		}
		$.post(url, $(this).serialize(), function (new_annotation) {
			fe.datastore.add_annotation(new_annotation);
			fe.logger.plot.redraw();
			$('#annotations-edit-dialog').fadeOut();
		}).fail(function () {

		});
	})
		.css("display", "flex")
		.hide()
		.fadeIn();

	$('#an_text').val(annotation.text)
		.focus();
}
var fe;

$(function () {
	'use strict';
	if (!fe) {
		fe = {};
	}
	if (!fe.logger) {
		fe.logger = {};
	}

	$(".progressBar").show();

	fe.logger.plot = (function () {
			var chart;

			var w, h;
			var xSc;
			var axis_channel_l;
			var axis_channel_r;

			var drag_handle_behaviour = null;
			var selection = {x: 0, w: 0, channels: [], start: 0, end: 0};
			var selector;
			var settings;

			function init(_selector, _settings) {
				selector = _selector;
				settings = _settings;

				// allow some pixels for right axis
				w = get_width();
				h = get_height();

				axis_channel_l = settings.axis_channel;
				axis_channel_r = settings.axis_channel;
			}

			var get_height = function () {
				return selector.height() - 150;
			};

			var get_width = function () {
				return selector.width() - 120;
			};

			var filter_channels = function (state) {
				// TODO Currently very inefficient!
				var datasets = fe.datastore.get_datasets();
				$.each(datasets, function (index, dataset) {
					var found = false;
					$.each(state, function (j, item) {
						if (item.channel == dataset.channel && item.sensor == dataset.sensor) {
							found = true;
						}
					});
					dataset.visible = found;
				});
				redraw();
				redraw_selection();
			};

			var set_axis_channel = function (channel, left) {
				if (left) {
					axis_channel_l = channel;
				}
				else {
					axis_channel_r = channel;
				}
				redraw();
			};

			var redraw_selection = function () {
				var datasets = fe.datastore.get_datasets();
				if (datasets.length > 0) {
					if (selection.w > 0) {
						create_selection(selection.x, selection.w, selection.channels);
					}
					select_datasets(selection.channels);
				}
			};

			var get_x_range = function () {
				var x_min = -1;
				var x_max = -1;
				$.each(fe.datastore.get_datasets(), function (index, dataset) {
					if (x_min == -1 || dataset.x_min < x_min) {
						x_min = dataset.x_min;
					}
					if (x_max == -1 || dataset.x_max > x_max) {
						x_max = dataset.x_max;
					}
				});
				return {min: x_min, max: x_max};
			};

			var get_y_scale = function (channel_id) {
				var y_min = -1;
				var y_max = -1;
				$.each(fe.datastore.get_datasets(), function (index, dataset) {
					if (dataset.channel == channel_id) {
						if (y_min == -1 || dataset.y_min < y_min) {
							y_min = dataset.y_min;
						}
						if (y_max == -1 || dataset.y_max > y_max) {
							y_max = dataset.y_max;
						}
					}
				});

				var pad = (y_max - y_min) / 10;

				y_max = y_max + pad;
				y_max = Math.ceil(y_max / 10) * 10;

				if (y_min > 0) {
					y_min = 0;
				} else {
					y_min = y_min - pad;
					y_min = Math.floor(y_min / 10) * 10;
				}

				return d3.scale.linear().domain([y_min, y_max]).range([0, h]);
			};

			var redraw = function () {
				var data;

				w = get_width();
				h = get_height();

				var x_range = get_x_range();
				xSc = d3.time.scale().domain([x_range.min, x_range.max]).range([0, w]);

				// clear any existing stuff (in case of refresh)
				d3.selectAll(selector.toArray()).select("svg").remove();

				// the selector div is defined in the html file
				chart = d3.selectAll(selector.toArray()).append("svg")
					.append("g")
					.attr("transform", "translate(60,42)");

				if (fe.datastore.get_datasets().length === 0) {
					chart.append("text")
						.attr("x", 200)
						.attr("class", "no_data_text")
						.attr("y", h / 3)
						.text('No data, yet');
					return;
				}

				draw_data();
				draw_x_axis();
				if (axis_channel_l || axis_channel_r) {
					draw_y_axis();
				}
				select_datasets(selection.channels);

				chart.append("svg:polyline")
					.attr('class', 'graph-axis')
					.attr("points", '0,0 0,' + h + ' ' + w + ',' + h + ' ' + w + ',0');

				draw_events();

				setup_interaction();
			};

			var draw_x_axis = function () {

				if (settings.draw_xlabels) {
					// draw horizontal axis labels
					chart.selectAll(".xRule")
						.data(xSc.ticks(10))
						.enter().append("text")
						.attr("class", "xRule")
						.attr("x", function (d) {
							return xSc(d);
						})
						.attr("y", h + 2 + 15)
						.attr("text-anchor", "middle")
						.text(xSc.tickFormat(10));

					chart.selectAll(".xTicks2")
						.data(xSc.ticks(20))
						.enter().append("line")
						.attr('class', 'graph-axis-mark')
						.attr("x1", xSc)
						.attr("x2", xSc)
						.attr("y1", h - 3)
						.attr("y2", h)
						.style("opacity", "0.3")
						.style("stroke", "#000");

					// draw horizontal axis ticks
					chart.selectAll(".xTicks")
						.data(xSc.ticks(10))
						.enter().append("line")
						.attr('class', 'graph-axis-mark')
						.attr("x1", xSc)
						.attr("x2", xSc)
						.attr("y1", h - 5)
						.attr("y2", h)
						.style("stroke", "#333");
				}
			};

			var draw_y_axis = function () {
				//// Left axis
				if (axis_channel_l) {
					var ySc_l = get_y_scale(axis_channel_l);
					var channel_l = fe.datastore.lookup_channel(axis_channel_l);

					if (channel_l) {
						chart.selectAll(".yTicks2-l")
							.data(ySc_l.ticks(20))
							.enter().append("line")
							.attr('class', 'graph-axis-mark')
							.attr("x1", 0)
							.attr("x2", 3)
							.attr("y1", function (d) {
								return h - ySc_l(d);
							})
							.attr("y2", function (d) {
								return h - ySc_l(d);
							})
							.style("opacity", "0.3")
							.style("stroke", "#000");

						// draw vertical axis "ticks" (they are actually grid lines)
						chart.selectAll(".yTicks-l")
							.data(ySc_l.ticks(10))
							.enter().append("line")
							.attr('class', 'graph-axis-mark')
							.attr("x1", 0)
							.attr("x2", 4)
							.attr("y1", function (d) {
								return h - ySc_l(d);
							})
							.attr("y2", function (d) {
								return h - ySc_l(d);
							})
							.style("stroke", "#333");

						// draw vertical axis labels
						chart.selectAll(".yRule-l")
							.data(ySc_l.ticks(10))
							.enter().append("text")
							.attr("class", "yRule-l")
							.attr("x", -5)
							.attr("y", function (d) {
								return h - ySc_l(d);
							})
							.attr("dy", 5)
							.attr("text-anchor", "end")
							.text(function (d) {
								return ySc_l.tickFormat(10, "s")(d) + channel_l.units;
							});
					}
				}
				//// Right axis

				if (axis_channel_r) {
					var ySc_r = get_y_scale(axis_channel_r);
					var channel_r = fe.datastore.lookup_channel(axis_channel_r);
					if (channel_r) {
						// draw vertical axis "ticks" (they are actually grid lines)
						chart.selectAll(".yTicks2-r")
							.data(ySc_r.ticks(20))
							.enter().append("line")
							.attr('class', 'graph-axis-mark')
							.attr("x1", w - 3)
							.attr("x2", w)
							.attr("y1", function (d) {
								return h - ySc_r(d);
							})
							.attr("y2", function (d) {
								return h - ySc_r(d);
							})
							.style("opacity", "0.3")
							.style("stroke", "#000");

						chart.selectAll(".yTicks-r")
							.data(ySc_r.ticks(10))
							.enter().append("line")
							.attr('class', 'graph-axis-mark')
							.attr("x1", w - 4)
							.attr("x2", w)
							.attr("y1", function (d) {
								return h - ySc_r(d);
							})
							.attr("y2", function (d) {
								return h - ySc_r(d);
							})
							.style("stroke", "#333");

						// draw vertical axis labels
						chart.selectAll(".yRule-r")
							.data(ySc_r.ticks(10))
							.enter().append("text")
							.attr("class", "yRule-r")
							.attr("x", w + 5)
							.attr("y", function (d) {
								return h - ySc_r(d);
							})
							.attr("dy", 5)
							.attr("text-anchor", "start")
							.text(function (d) {
								return ySc_r.tickFormat(10, "s")(d) + channel_r.units;
							});
					}
				}
			};

			var draw_data = function () {
				var data_sets = fe.datastore.get_datasets();

				$.each(data_sets, function (index, data_set) {
					var ySc = get_y_scale(data_set.channel);
					var d3line = d3.svg.line()
						.x(function (d) {
							return xSc(d.time);
						})
						.y(function (d) {
							return h - ySc(d.value);
						});

					var line = chart.append("svg:path")
						.attr('class', 'graph-line')
						.style("stroke", data_set.colour)
						.attr("d", d3line(data_set.data));

					if (!data_set.visible) {
						line.style("display", "none");
					}
				});
			};

			var draw_antievents = function () {
				var x_range = get_x_range();
				var antiEvents = [{
					start: x_range.min,
					end: x_range.max
				}];

				var mouseG = chart.append("g")
					.attr("class", "mouse-over-effects");

				mouseG.append("path")
					.attr("class", "mouse-line")
					.style("stroke", "black")
					.style("stroke-width", "1px")
					.style("opacity", "0");

				var data_sets = fe.datastore.get_datasets();

				var mousePerLine = mouseG.selectAll('.mouse-per-line')
					.data(data_sets)
					.enter()
					.append("g")
					.attr("class", "mouse-per-line");

				mousePerLine.append("circle")
					.attr("r", 5)
					.style("stroke", function (d) {
						return d.colour;
					})
					.style("fill", "none")
					.style("stroke-width", "1px")
					.style("opacity", "0");

				mousePerLine.append("text")
					.attr("transform", "translate(10,3)")
					.style("font-size", "13px")
					.attr("fill", "#444");


				// the .bgs are used for listening to drag events
				// they are the segments of the graph between events
				chart.selectAll('.graph-bg').remove();

				chart.selectAll('.graph-bg')
					.data(antiEvents).enter()
					.append("rect")
					.attr('class', 'graph-bg')
					.attr("y", 0)
					.attr("x", function (d) {
						return xSc(d.start);
					})
					.attr("height", h)
					.attr("width", function (d) {
						return xSc(d.end) - xSc(d.start);
					});

				setup_interaction();
			};

			var get_flat_annotations = function () {
				var flat_annotations = [];
				$.each(fe.datastore.get_annotations(), function (key, annotation) {
					flat_annotations.push(annotation);
				});

				// Sort the events chronologically
				flat_annotations = flat_annotations.sort(function (a, b) {
					return a.start - b.start;
				});

				// Filter out any which end too far to the lhs of the plot
				flat_annotations = flat_annotations.filter(function (d) {
					return xSc(d.end) > 10;
				});
				return flat_annotations;
			};

			var draw_events = function () {
				var flat_annotations = get_flat_annotations();
				fe.logger.annotation.draw_events(flat_annotations);

				draw_antievents();
			};

			var get_chart = function () {
				return chart;
			};

			var limit_bounds = function (container, x0, x1) {
				var cntX, cntW, w;

				cntX = parseFloat(container.attr('x'));
				cntW = parseFloat(container.attr('width'));
				// constrain x1 to the container (x0 is bound to be inside,
				// because that's a click event)
				// (i.e. x1 is at most the rhs of the container,
				// at least the lhs of the container)
				x1 = Math.max(cntX, Math.min(cntW + cntX - 1, x1));

				w = x1 - x0;

				if (w < 0) {
					x0 = x1;
					w = -w;
				}
				return {'x': x0, 'w': w};
			};

			var clear_selection = function (trigger_events) {
				if (typeof trigger_events === 'undefined') {
					trigger_events = true;
				}
				if (trigger_events) {
					$("#chart").trigger("logger:click", {
						'button': 'clear_selection',
						'params': {}
					});
				}
				selection.x = 0;
				selection.w = 0;
				selection.channels = [];
				chart.selectAll('.selection').remove();
				chart.selectAll('.selection_handle').remove();
				var data_sets = fe.datastore.get_datasets();
				$.each(data_sets, function (index, dataset) {
					dataset.selected = false;
				});
				select_datasets(selection.channels);
			};

			var resize_selection = function (x, w) {
				selection.x = x;
				selection.w = w;
				selection.start = moment(get_time_for_x(x));
				selection.end = moment(get_time_for_x(x + w));

				// Update the width of the selection.
				chart.selectAll('.selection')
					.attr('x', x)
					.attr("width", w);

				// Move the drag handles, and labels, to the correct positions.
				chart.selectAll('.selection_handle.end')
					.attr("x", x + w - 10);
				chart.selectAll('.selection_handle.start')
					.attr("x", x);

				chart.selectAll('.selection_handle.start.label')
					.attr("x", x - 5)
					.text('start: ' + selection.start.format('H:mm'));
				chart.selectAll('.selection_handle.end.label')
					.attr("x", x + w + 5)
					.text('end: ' + selection.end.format('H:mm'));

			};

			var create_selection = function (x, w, selections, trigger_events) {

				if (typeof trigger_events === 'undefined') {
					trigger_events = true;
				}

				clear_selection(false);

				resize_selection(x, w);
				selection.channels = selections;

				select_datasets(selection.channels);

				// Create a new selection rectangle, initially with width 1px.
				chart.append('rect')
					.attr('class', 'selection')
					.attr("y", 0)
					.attr("height", h)
					.attr("x", selection.x)
					.attr("width", selection.w)
					.attr("opacity", "0.5");

				if (settings.handles) {
					// Draw left drag handle.
					chart.append('svg:image')
						.attr("xlink:href", server_url + 'images/selection_handle.svg')
						.attr('class', 'selection_handle start')
						.attr("y", h / 2 - 12)
						.attr("height", 24)
						.attr("x", selection.x)
						.attr("width", 12);

					selection.start = moment(get_time_for_x(selection.x));
					selection.end = moment(get_time_for_x(selection.x + selection.w));

					// Add text at left of selection
					chart.append('text')
						.attr('class', 'selection_handle start label')
						.attr("y", h / 2 - 30)
						.attr("x", selection.x - 5)
						.attr("fill", "black")
						.attr("text-anchor", "end")
						.text('start: ' + selection.start.format('H:mm'));

					// Draw right drag handle.
					chart.append('svg:image')
						.attr("xlink:href", server_url + 'images/selection_handle.svg')
						.attr('class', 'selection_handle end')
						.attr("y", h / 2 - 12)
						.attr("height", 24)
						.attr("x", selection.x + selection.w - 12)
						.attr("width", 12);

					// Add text at right of selection
					chart.append('text')
						.attr('class', 'selection_handle end label')
						.attr("y", h / 2 - 30)
						.attr("x", selection.x + selection.w + 5)
						.attr("fill", "black")
						.attr("text-anchor", "start")
						.text('end: ' + selection.end.format('H:mm'));


					// Add drag behaviour for handles.
					d3.selectAll('.selection_handle').call(drag_handle_behaviour);
				}

				if (trigger_events) {
					$("#chart").trigger("logger:click", {
						'button': 'create_selection',
						'params': {}
					});
				}
				// enable_selection_click();
			};

			var on_selection_click = function () {
				var event = {}, temp;

				if (d3.event) {
					d3.event.preventDefault();
				}
				var x = selection.x;
				var w = selection.w;

				event.start = get_time_for_x(x);
				event.end = get_time_for_x(x + w);

				if (event.start >= event.end) {
					temp = event.start;
					event.start = event.end;
					event.end = temp;
				}

				event.delta = event.end.getTime() - event.start.getTime();

				var pairs = [];
				// Store the selected channels.
				$.each(fe.datastore.get_datasets(), function (index, dataset) {
					if (dataset.selected) {
						pairs.push({
							'sensor': {'id': dataset.sensor},
							'channel': {'id': dataset.channel}
						});
					}
				});

				event.pairs = pairs;
			};

			var enable_selection_click = function () {
				chart.selectAll('.selection')
					.on('contextmenu', on_selection_click)
					.on('click', on_selection_click);
			};

			var select_datasets = function (selection) {
				var data_sets = fe.datastore.get_datasets();

				// Deselect everything
				$.each(data_sets, function (index, dataset) {
					dataset.selected = false;
				});

				// Select ones to show
				$.each(selection, function (index, value) {
					data_sets[value].selected = true;
				});
				d3.selectAll('path.linechart').classed("filtered", function (d, i) {
					return selection.indexOf(i) == -1;
				});
			};

			// interaction
			// create a new nested scope to avoid variables mess
			var setup_interaction = function () {
				var container = null;

				var drag_handle_move = function () {
					var x0, x1, w;

					// get the container horizontal bounds
					var cntX = parseFloat(container.attr('x'));
					var cntW = parseFloat(container.attr('width'));

					var handle_x = parseFloat(d3.select(this).attr('x'));
					var handles_coords = d3.selectAll('image.selection_handle')[0].map(function (d) {
						return parseFloat(d3.select(d).attr('x'));
					});

					var newX = parseFloat(chart.select('.selection').attr('x'));

					if (handle_x === d3.max(handles_coords)) {
						// right (end) handle
						x0 = newX;
						x1 = fe.logger.selection.mouse_x(this);
						// constrain x1 to the container (x0 is bound to be inside,
						// because that's a click event)
						x1 = Math.max(cntX, Math.min(cntW + cntX, x1));
					} else {
						// left (start) handle
						w = parseFloat(chart.select('.selection').attr('width'));

						x0 = fe.logger.selection.mouse_x(this);
						x1 = newX + w;

						x0 = Math.max(cntX, Math.min(cntW + cntX, x0));
					}

					w = x1 - x0;

					if (w < 0) {
						x0 = x1;
						w = -w;
					}

					resize_selection(x0, w);
				};

				d3.selectAll('.graph-bg')
					.on('mouseout', function () { // on mouse out hide line, circles and text
						d3.select(".mouse-line")
							.style("opacity", "0");
						d3.selectAll(".mouse-per-line circle")
							.style("opacity", "0");
						d3.selectAll(".mouse-per-line text")
							.style("opacity", "0");
					})
					.on('mouseover', function () { // on mouse in show line, circles and text
						d3.select(".mouse-line")
							.style("opacity", "0.2");
						d3.selectAll(".mouse-per-line circle")
							.style("opacity", "1");
						d3.selectAll(".mouse-per-line text")
							.style("opacity", "1");
					})
					.on('mousemove', function () { // mouse moving over canvas
						var mouse = d3.mouse(this);
						d3.select(".mouse-line")
							.attr("d", function () {
								var d = "M" + mouse[0] + "," + get_height();
								d += " " + mouse[0] + "," + 0;
								return d;
							});

						d3.selectAll(".mouse-per-line")
							.attr("transform", function (d) {
								if (!d.visible) {
									return "translate(-1000,-1000)";
								}
								var xDate = moment(xSc.invert(mouse[0]));
								var maxIndex = d.data.length - 1;
								if (d.data[0].time < xDate && d.data[maxIndex].time > xDate) {
									var index = 0;
									while (index != maxIndex) {
										var currentIndex = (index + maxIndex) / 2 | 0;
										if (d.data[currentIndex].time > xDate) {
											maxIndex = currentIndex;
											if (d.data[currentIndex - 1].time <= xDate) {
												index = currentIndex - 1;
												break;
											}
										} else {
											index = currentIndex;
											if (d.data[currentIndex + 1].time > xDate) {
												maxIndex = currentIndex + 1;
												break;
											}
										}
									}

									var pos = fe.datastore.get_position(d.data[index], d.data[maxIndex], xDate);
									d3.select(this).select('text').text(pos.toFixed(2) + d.units);

									var ySc = get_y_scale(d.channel);
									return "translate(" + mouse[0] + "," + (h - ySc(pos)) + ")";
								}

								return "translate(-1000,-1000)";
							});
					});

				if (settings.enable_selection) {
					var drag_behaviour = d3.behavior.drag()
						.on("dragstart", function () {
							fe.logger.selection.drag_start(this);
						})
						.on("drag", function () {
							fe.logger.selection.drag_move(this);
						})
						.on("dragend", function () {
							fe.logger.selection.drag_end(this);
						});

					d3.selectAll('.graph-bg').call(drag_behaviour);
				}

				drag_handle_behaviour = d3.behavior.drag()
					.on("dragstart", function () {

						d3.selectAll('.graph-bg').call(drag_handle_aux_behaviour);

						// find the bg container we are in
						d3.selectAll('.graph-bg').each(function () {
							var cx, bg_x, bg_w, bg_rhs, curr = d3.select(this);
							cx = fe.logger.selection.mouse_x(this);
							bg_x = parseInt(curr.attr('x'), 10);
							bg_w = parseInt(curr.attr('width'), 10);
							bg_rhs = bg_x + bg_w;
							if (cx >= bg_x &&
								cx <= bg_rhs) {
								container = curr;
							}
						});

					})
					.on("dragend", function () {
						fe.logger.selection.drag_end(this);
						d3.selectAll('.graph-bg').call(drag_behaviour);
					})
					.on("drag", drag_handle_move);

				var drag_handle_aux_behaviour = d3.behavior.drag()
					.on("drag", drag_handle_move);
			};

			var get_selection = function () {
				return selection;
			};

			var get_x_for_time = function (t) {
				return xSc(t);
			};

			var get_time_for_x = function (x) {
				var t = xSc.invert(x);
				t.setMilliseconds(0);
				t.setMinutes((t.getMinutes() + t.getSeconds() / 60).toFixed(0));
				return t;
			};

			// export the API
			return {
				init: init,
				redraw: redraw,
				clear_selection: function (trigger_events) {
					clear_selection(trigger_events);
				},
				create_selection: function (x, w, selections, trigger_events) {
					create_selection(x, w, selections, trigger_events);
				},
				resize_selection: function (x, w) {
					resize_selection(x, w);
				},
				limit_bounds: function (container, x0, x1) {
					return limit_bounds(container, x0, x1);
				},
				enable_selection_click: function () {
					enable_selection_click();
				},
				get_selection: function () {
					return get_selection();
				},
				get_chart: function () {
					return get_chart();
				},
				get_time_for_x: function (x) {
					return get_time_for_x(x);
				},
				get_x_for_time: function (t) {
					return get_x_for_time(t);
				},
				get_width: function () {
					return get_width();
				},
				get_height: function () {
					return get_height();
				},
				filter_channels: function (state) {
					return filter_channels(state);
				},
				set_axis_channel: function (channel, left) {
					return set_axis_channel(channel, left);
				},
				draw_events: function (suggestions) {
					return draw_events(suggestions);
				},
				draw_antievents: function () {
					return draw_antievents();
				}
			};
		}()
	);
});

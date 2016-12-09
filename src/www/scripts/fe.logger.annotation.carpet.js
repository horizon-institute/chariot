var fe;
$(function () {
	'use strict';
	if (!fe) {
		fe = {};
	}

	if (!fe.logger) {
		fe.logger = {};
	}

	fe.logger.annotation = (function () {
		var carpet;
		var selected_layer = null;

		return {
			get_selected_layer: function () {
				return selected_layer;
			},
			draw_events: function (annotations) {
				var plot = fe.logger.plot;
				var chart = plot.get_chart();
				var w = plot.get_width();
				var h = 150;
				var bar_h = 20;

				// Add carpet group
				carpet = chart.append("g")
					.attr("transform", "translate(0," + (plot.get_height() + 40) + ")")
					.attr("height", h)
					.attr("width", w)
					.attr("class", "carpet");

				// Remove existing events from rects
				chart.selectAll('.graph-annotation').remove();
				carpet.selectAll('.carpet-annotation').remove();

				// Set up carpet
				var layers = [
					{
						"ref": 1,
						"colour": "#c62828"
					},
					{
						"ref": 2,
						"colour": "#2E7D32"
					},
					{
						"ref": 3,
						"colour": "#1565C0"
					}
				];

				var groups = carpet.selectAll(".carpet-row")
					.data(layers)
					.enter()
					.append("g");

				// Add background rectangles to carpet
				groups.append("rect")
					.attr("class", "carpet-row")
					.attr("x", 0)
					.attr("y", function (layers, i) {
						return i * bar_h;
					})
					.attr("width", w)
					.attr("height", function () {
						return bar_h;
					})
					.attr("fill", function (layers) {
						return layers.colour;
					})
					.style("opacity", 0.3)
					.on('click', function (layer) {
						selected_layer = layer;
						d3.selectAll('.carpet-row').style("opacity", 0.3);
						d3.select(this).style("opacity", 1);
						fe.logger.plot.draw_antievents();
					});

				if (selected_layer == null) {
					console.log("First time");
					selected_layer = layers[0];
				}

				var selected_row = $(".carpet-row")[selected_layer.ref - 1];
				// TODO: Put this into a separate function
				d3.selectAll('.carpet-row').style("opacity", 0.3);
				d3.select(selected_row).style("opacity", 1);

				// Add annotations
				var carpetEventNodes = carpet.selectAll('.carpet-annotation')
					.data(annotations);

				// Handle events
				carpetEventNodes.enter()
					.append("rect")
					.attr('class', function (d) {
						var c;
						c = 'carpet-annotation';
						return c + ' _' + d.id;
					})
					.attr("x", function (d) {
						return fe.logger.plot.get_x_for_time(moment(d.start));
					})
					.attr("fill", "#000")
					.style('opacity', 0.4)
					.attr("height", bar_h)
					.attr("y", function (d) {
						return (d.layer - 1) * bar_h;
					})
					.attr("width", function (d) {
						var x0 = fe.logger.plot.get_x_for_time(moment(d.start));
						var x1 = fe.logger.plot.get_x_for_time(moment(d.end));
						return x1 - x0;
					})
					.on('click', function (e) {
						show_annotation_editor(e);
						d3.event.preventDefault();
						d3.event.stopPropagation();
					});


				var chartEventNodes = chart.selectAll('.graph-annotation')
					.data(annotations);

				// Create selection rectangle
				chartEventNodes.enter().append('rect')
					.attr('class', function (d) {
						var c;
						c = 'graph-annotation';
						return c + ' _' + d.id;
					})
					.attr("y", 0)
					.attr("height", plot.get_height())
					.attr("x", function (d) {
						return fe.logger.plot.get_x_for_time(moment(d.start));
					})
					.attr("width", function (d) {
						var x0 = fe.logger.plot.get_x_for_time(moment(d.start));
						var x1 = fe.logger.plot.get_x_for_time(moment(d.end));
						return x1 - x0;
					}).on('click', function (e) {
						show_annotation_editor(e);
						d3.event.preventDefault();
						d3.event.stopPropagation();
					});
			}
		};
	}());
});
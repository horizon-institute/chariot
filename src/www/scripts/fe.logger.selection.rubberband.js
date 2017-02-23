var fe;
$(function () {
	'use strict';
	if (!fe) {
		fe = {};
	}

	if (!fe.logger) {
		fe.logger = {};
	}

	fe.logger.selection = (function () {
		var selections = [];
		var drag_start;
		var dragging = false;

		return {
			mouse_x: function (container) {
				var touches = d3.touches(container);
				return touches.length > 0 ? touches[0][0] : d3.mouse(container)[0];
			},

			drag_start: function (instance) {
				selections = [];
				var ds = fe.datastore.get_datasets();
				$.each(ds, function (index, dataset) {
					if (dataset.visible) {
						selections.push(index);
					}
				});

				fe.logger.plot.clear_selection();
				drag_start = this.mouse_x(instance);
				dragging = false;
			},

			drag_move: function (instance) {
				var plot = fe.logger.plot;
				var bounds = plot.limit_bounds(d3.select(instance), drag_start, this.mouse_x(instance));

				if (!dragging && bounds.w > 10) {
					dragging = true;
					plot.create_selection(bounds.x, bounds.w, selections, false);
				}
				else if (dragging) {
					plot.resize_selection(bounds.x, bounds.w);
				}
				plot.get_selection().dragX = bounds.x;
				plot.get_selection().dragW = bounds.w;
			},

			drag_end: function () {
				// If width is too small, bail.
				if (dragging) {
					var plot = fe.logger.plot;
					var x = plot.get_selection().dragX;
					var w = plot.get_selection().dragW;

					if (Math.abs(w) <= 10) {
						plot.clear_selection(true);
						return;
					}

					plot.resize_selection(x, w);
					plot.enable_selection_click();
					plot.create_selection(x, w, selections, true);
				}
				else {
	            	// TODO Handle clicking
				}
			}
		};
	}());
});
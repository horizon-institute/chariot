var fe;
if (!fe) {
    fe = {};
}

$(function () {
    'use strict';

    var settings;

    var methods = {
    	init: function(options) {

		    var selector = this;
		    settings = $.extend({
		    	antievents: true,
		    	handles: true,
		    	make_events: true,
			    all_channels: false,
		    	enable_selection: true,
		    	selection: fe.logger.selection,
		    	annotation: fe.logger.annotation,
		    	ui: fe.logger.ui,
		    	draw_controls: true,
		    	enabled_annotation: 1,
		    	hide_unannotated: false,
		    	draw_xlabels: true,
		    	callback: undefined,
		    	axis_channel: 0,
		    	layers: [],
		    	colours: [
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
			    ]
		    }, options);

	    	fe.logger.plot.init(selector, settings);
		    return this;
    	}
    };

    $.fn.logger = function(options) {
   		return methods.init.apply(this, options);
	};
});


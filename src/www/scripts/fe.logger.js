var fe;
if (!fe) {
    fe = {};
}

$(function () {
    'use strict';

    var m_plot = null,
        settings;

    var methods = {
    	init: function(options) {
		    
		    var selector = this;
		    m_plot = fe.logger.plot;

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
		    
		    //-------------------------------------------------------
		    
		    $('.nav .logger').addClass('selected');

		    return this;
    	},
    	filterChannels: function(channels) {
    		fe.logger.plot.filter_channels(channels);
    		fe.logger.plot.redraw();
    		fe.logger.plot.redraw_selection();
    	}
    };

    $.fn.logger = function(methodOrOptions) {
		console.log(methodOrOptions);
    	if(methods[methodOrOptions]) {
    		return methods[methodOrOptions].apply(this, Array.prototype.slice.call(arguments, 1));
    	}
    	else if(typeof methodOrOptions === 'object' || !methodOrOptions) {
			console.log(methods);
    		return methods.init.apply(this, arguments);
    	}
	};
});


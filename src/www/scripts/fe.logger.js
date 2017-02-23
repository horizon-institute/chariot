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
		    	antievents: false,
		    	handles: true,
			    all_channels: false,
		    	enable_selection: true,
		    	draw_xlabels: true,
		    	axis_channel: 0,
		    	layers: []
		    }, options);

	    	fe.logger.plot.init(selector, settings);
		    return this;
    	}
    };

    $.fn.logger = function(options) {
   		return methods.init.apply(this, options);
	};
});


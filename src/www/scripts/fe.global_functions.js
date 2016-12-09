// TODO: modify this code so that protypes are added only if they
// are not already there (ecmascript 5 browsers)

$.ajaxSetup({
	cache: false,
	timeout: 10000
});

var fe;
if (!fe) {
    fe = {};
}

if(!Array.prototype.last) {
    Array.prototype.last = function () {
        'use strict';
        return this[this.length - 1];
    };
}

/**
 * Extends the Array object to allow searching within the array.
 */
if(!Array.prototype.find) {
    Array.prototype.find = function (f) {
        'use strict';
        var i;
        for (i = 0; i < this.length; i += 1) {
            if (f(this[i]) === true) {
                return i;
            }
        }
        return -1;
    };
}
    
/**
 * Extends the Date object to allow date formats
 * @param specififed format
 */
Date.prototype.format = function (format) {
    'use strict';
    // Format="YYYY-MM-dd hh:mm:ss";
    var o, month_names, k;
    month_names = 'January February March April May June July August September October November December';
    month_names = month_names.split(' ');
    o = {
        "N+":  month_names[this.getMonth()], //month
        "M+":  this.getMonth() + 1, //month
        "d+":  this.getDate(), //day
        "h+":  this.getHours(), //hour
        "m+":  this.getMinutes(), //minute
        "s+":  this.getSeconds(), //second
        "q+":  Math.floor((this.getMonth() + 3) / 3),  //quarter
        "S":  this.getMilliseconds() //millisecond
    };
    
    if (/(y+)/.test(format)) { 
        format = format.replace(RegExp.$1, (this.getFullYear() + String()).substr(4 - RegExp.$1.length));
    }
    for (k in o) {
        if (o.hasOwnProperty(k)){
            if (new RegExp("(" + k + ")").test(format)) {
                format = format.replace(RegExp.$1, RegExp.$1.length === 1 ? o[k] : ("00" + o[k]).substr((String() + o[k]).length));
            }
        }
    }
    return format;    
};

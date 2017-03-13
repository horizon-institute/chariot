var express = require('express');
var router = express.Router();
var macaddress = require('macaddress');

var request = require('request');
var fs = require('fs');
request = request.defaults({jar: true});

var token = 's';

var requestPause = 1000;

var url = 'http://34.251.188.176';
var local_mac = '00:00:00:00:00:00'; // 
var tokenUrl = url + "/api/hub/" +  local_mac + "/token";
var currentData;

function updateToken(){

	macaddress.one('eth0', function (err, mac) {
  		local_mac = mac;
		tokenUrl = url + "/api/hub/" +  local_mac + "/token";
		console.log("Mac address for eth0: %s", mac);  
		console.log(this.currentData);
		request(tokenUrl, function(error, response, body){
			var stuff = JSON.parse(body);
			token = "Token " + stuff.token;
			console.log(token);
			pushData();
			pingHub(local_mac);
		});
	});
}

function sendData(mac_address, sensor_id, channel_name, reading) {
	
	return new Promise(function (resolve, reject) {
		var requestData = {
			url: url + '/api/reading',
			formData: {
				hub: mac_address,
				sensor: sensor_id,
				channel: channel_name,
				value: reading
			},
			headers: {
				'Authorization': token
			}
		};
		console.log(token);

		request
			.post(requestData, function (err, response, body) {
				
				if (err != null) {
					console.log(JSON.stringify(response));
					console.log("Error " + err + " (" + duration + " ms" + ")");
				} else if (response.statusCode != 201) {
					console.log("Error " + response.statusCode + " sending sensor reading: POST " + requestData.url + ": " + JSON.stringify(requestData.formData));
					fs.writeFile("error.html", body, function (err) {
						if (err) {
							return console.log(err);
						}
					});
				} else {
					
				}
				
			});
	});
}


function pingHub(mac_address) {
	var requestData = {
		url: url + '/api/hub/' + mac_address + '/ping',
		headers: {
			'Authorization': token
		}
	};
	request
		.put(requestData, function (err, response, body) {
			if (err != null) {
				console.log("Error " + err);
			} else if (response.statusCode != 200) {
				console.log("Error " + response.statusCode + " sending hub alive message: PUT " + requestData.url);
				fs.writeFile("error.html", body, function (err) {
					if (err) {
						return console.log(err);
					}
				});
			}
			
		});
}

function pushData() {
	var array = this.currentData;
	if(array[0][1] == 7) {
	console.log("timestamp: " + array[0][0]);
	console.log("node id: " + array[0][1]);
	console.log("Power 1: " + array[0][2] + "W");
	console.log("Power 2: " + array[0][3] + "W");
	console.log("Power 3: " + array[0][4] + "W");
	console.log("Power 4: " + array[0][5] + "W");
	console.log("rssi: " + array[0][15]);
	
	if (array[0][2] > 0){
		sendData(local_mac, '7', 'ELEC', String(array[0][2]));
		sendData(local_mac, '7', 'BATT', '2.4');
		sendData(local_mac, '7', 'RSSI', String(array[0][15]));
	}

	if (array[0][3] > 0){
		sendData(local_mac, '8', 'ELEC', String(array[0][3]));
		sendData(local_mac, '8', 'BATT', '2.4');
		sendData(local_mac, '8', 'RSSI', String(array[0][15]));
	}

	if (array[0][4] > 0){
		sendData(local_mac, '9', 'ELEC', String(array[0][4]));
		sendData(local_mac, '9', 'BATT', '2.4');
		sendData(local_mac, '9', 'RSSI', String(array[0][15]));
	}

	if (array[0][5] > 0){
		sendData(local_mac, '10', 'ELEC', String(array[0][5]));
		sendData(local_mac, '10', 'BATT', '2.4');
		sendData(local_mac, '10', 'RSSI', String(array[0][15]));
	}

}

if(array[0][1] == 23) {
	console.log("timestamp: " + array[0][0]);
	console.log("node id: " + array[0][1]);
	console.log("internal temp: " + array[0][2]/10 + "ºC");
	console.log("external temp: " + array[0][3]/10 + "ºC");
	console.log("humidity: " + array[0][4]/10 + "%");
	console.log("battery: " + array[0][5]/10 + "V");
	console.log("rssi: " + array[0][8]);
	sendData(local_mac, String(array[0][1]), 'TEMP', String(array[0][3]/10));
	sendData(local_mac, String(array[0][1]), 'BATT', String(array[0][5]/10));
	sendData(local_mac, String(array[0][1]), 'RSSI', String(array[0][8]));
}
if(array[0][1] == 24) {
	console.log("timestamp: " + array[0][0]);
	console.log("node id: " + array[0][1]);
	console.log("internal temp: " + array[0][2]/10 + "ºC");
	console.log("external temp: " + array[0][3]/10 + "ºC");
	console.log("humidity: " + array[0][4]/10 + "%");
	console.log("battery: " + array[0][5]/10 + "V");
	console.log("rssi: " + array[0][8]);
	sendData(local_mac, String(array[0][1]), 'TEMP', String(array[0][2]/10));
	sendData(local_mac, String(array[0][1]), 'HUMI', String(array[0][4]/10));
	sendData(local_mac, String(array[0][1]), 'BATT', String(array[0][5]/10));
	sendData(local_mac, String(array[0][1]), 'RSSI', String(array[0][8]));
}
if(array[0][1] == 25) {
	console.log("timestamp: " + array[0][0]);
	console.log("node id: " + array[0][1]);
	console.log("internal temp: " + array[0][2]/10 + "ºC");
	console.log("external temp: " + array[0][3]/10 + "ºC");
	console.log("humidity: " + array[0][4]/10 + "%");
	console.log("battery: " + array[0][5]/10 + "V");
	console.log("rssi: " + array[0][8]);
	sendData(local_mac, String(array[0][1]), 'TEMP', String(array[0][2]/10));
	sendData(local_mac, String(array[0][1]), 'HUMI', String(array[0][4]/10));
	sendData(local_mac, String(array[0][1]), 'BATT', String(array[0][5]/10));
	sendData(local_mac, String(array[0][1]), 'RSSI', String(array[0][8]));
}
if(array[0][1] == 26) {
	console.log("timestamp: " + array[0][0]);
	console.log("node id: " + array[0][1]);
	console.log("internal temp: " + array[0][2]/10 + "ºC");
	console.log("external temp: " + array[0][3]/10 + "ºC");
	console.log("humidity: " + array[0][4]/10 + "%");
	console.log("battery: " + array[0][5]/10 + "V");
	console.log("rssi: " + array[0][8]);
	sendData(local_mac, String(array[0][1]), 'TEMP', String(array[0][2]/10));
	sendData(local_mac, String(array[0][1]), 'HUMI', String(array[0][4]/10));
	sendData(local_mac, String(array[0][1]), 'BATT', String(array[0][5]/10));
	sendData(local_mac, String(array[0][1]), 'RSSI', String(array[0][8]));
}

}

router.post('/input/bulk.json', function(req, res, next) {
	console.log("foo");
	this.currentData = JSON.parse(req.body.data);
	updateToken();
	res.sendStatus(200);
});
module.exports = router;

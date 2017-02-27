const fetch = require('node-fetch');
const FormData = require('form-data');
const fs = require('fs');
const assert = require('assert');

const requestPause = 1000;

const url = 'http://localhost';
const mac_addresses = ['12:34:56:78:90:01'];
const sensors = ['7','23','24','25'];
const channels = []; // Empty for all channels
var headers = {};

fetch(url + '/api/hub/' + mac_addresses[0] + '/token')
	.then(function (response) {
		assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
		return response.json();
	})
	.then(function (json) {
		headers = {
			'Authorization': 'Token ' + json.token
		};
		return fetch(url + '/api/deployments', {headers: headers});
	})
	.then(function (response) {
		assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
		return response.json();
	})
	.then(function (deploymentList) {
	    console.log(JSON.stringify(deploymentList));
		var deploymentIndex = 0;
		var sensorIndex = 0;
		var channelIndex = 0;

		const deployments = [];
		for (const deployment of deploymentList) {
			const index = mac_addresses.indexOf(deployment.hub);
			if (index != -1) {
				deployments.push(deployment);
			}
		}

		assert(deployments.length > 0, 'No active deployments');

		const interval = setInterval(function () {
			while (true) {
				const deployment = deployments[deploymentIndex];
				const sensor = deployment.sensors[sensorIndex].sensor;
				const channel = sensor.channels[channelIndex];
				channelIndex += 1;
				if (channelIndex >= sensor.channels.length) {
					channelIndex = 0;
					sensorIndex += 1;
					if (sensorIndex >= deployment.sensors.length) {
						fetch(url + '/api/hub/' + deployment.hub + '/ping', {method: 'PUT', headers: headers})
							.then(function (response) {
								assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
								process.stdout.write("\n");
								console.log(deployment.hub);
							});
						sensorIndex = 0;
						deploymentIndex += 1;
						if (deploymentIndex >= deployments.length) {
							deploymentIndex = 0;
						}
					}
				}

				if ((sensors.length == 0 || sensors.indexOf(sensor.id) != -1)
				 && (channels.length == 0 || channels.indexOf(channel.id) != -1)) {
					sendData(deployment, sensor, channel, headers)
						.then(function (response) {
							assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
							process.stdout.write(".");
							return response.text()
                        })
                        .then(function (text) {
                            //console.log(text);
                        })
						.catch(function (err) {
		                    console.log('Error ' + err.message);
	                    });

					break;
				}
			}
		}, requestPause);
	})
	.catch(function (err) {
		console.log("Error " + err);
	});

function sendData(deployment, sensor, channel) {
	if (!channel.value) {
		channel.trend = 0;
		channel.value = 20;
	}
	else {
	    channel.trend += (Math.random() - Math.random()) / 1000;
	    channel.trend = Math.min(0.1, channel.trend);
		channel.trend = Math.max(-0.1, channel.trend);
		channel.value += channel.trend;
	}
	var data = new FormData();
	data.append('deployment', deployment.id);
	data.append('sensor', sensor.id);
	data.append('channel', channel.id);
	data.append('value', channel.value);
	return fetch(url + '/api/reading', {
		method: 'POST',
		body: data,
		headers: headers
	});
}



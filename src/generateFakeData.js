const fetch = require('node-fetch');
const FormData = require('form-data');
const fs = require('fs');
const assert = require('assert');

const requestPause = 1000;

const url = 'http://localhost';
const mac_addresses = ['12:34:56:78:90:01', '12:34:56:78:90:02'];
const channels = ['TEMP', 'ELEC']; // Empty for all channels
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
		var deploymentIndex = 0;
		var sensorIndex = 0;
		var channelIndex = 0;

		const deployments = [];
		for (const deployment of deploymentList) {
			const index = mac_addresses.indexOf(deployment.hub.mac_address);
			if (index != -1) {
				deployments.push(deployment);
			}
		}

		assert(deployments.length > 0, 'No active deployments');

		const interval = setInterval(function () {
			while (true) {
				const deployment = deployments[deploymentIndex];
				const sensor = deployment.sensors[sensorIndex];
				const channel = sensor.channels[channelIndex];
				channelIndex += 1;
				if (channelIndex >= sensor.channels.length) {
					channelIndex = 0;
					sensorIndex += 1;
					if (sensorIndex >= deployment.sensors.length) {
						fetch(url + '/api/hub/' + deployment.hub.mac_address + '/ping', {method: 'PUT', headers: headers})
							.then(function (response) {
								assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
								process.stdout.write("\n");
								console.log(deployment.hub.mac_address);
							});
						sensorIndex = 0;
						deploymentIndex += 1;
						if (deploymentIndex >= deployments.length) {
							deploymentIndex = 0;
						}
					}
				}

				if (channels.length == 0 || channels.indexOf(channel.name) != -1) {
					sendData(deployment, sensor, channel, headers)
						.then(function (response) {
							assert(response.ok, response.status + ': ' + response.statusText + ' ' + response.url);
							process.stdout.write(".");
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
		channel.value = 20;
	}
	else {
		channel.value += Math.random() - Math.random() + Math.random() - Math.random();
	}
	var data = new FormData();
	data.append('hub', deployment.hub.mac_address);
	data.append('sensor', sensor.identifier);
	data.append('channel', channel.name);
	data.append('value', channel.value);
	return fetch(url + '/api/reading', {
		method: 'POST',
		body: data,
		headers: headers
	});
}



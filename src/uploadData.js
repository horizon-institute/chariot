const fs = require('fs');
const moment = require('moment');
const fetch = require('node-fetch');
const lineReader = require('line-reader');

const url = "http://localhost:8086";
const batches = 5000;
var batch = "";
var index = 0;
var deployment = 4;

lineReader.eachLine('data.txt', function(line, last, cb) {
	if (!line.startsWith('name\ttimestamp')) {
		const items = line.split('\t');
		const item = items[0] + ',deployment=' + deployment + ',sensor=' + items[3] + ' value=' + items[2] + ' ' + moment(items[1], "YYYY-MM-DD HH:mm:ss").valueOf() + '\n';
		if (items[4] != '8') {
			console.log(items[4]);
		}
		batch = batch + item;
		index++;
		if (index > batches) {
			const text = batch;
			batch = "";
			index = 0;
			send(text, cb);
		}
		else {
			cb();
		}
	}
	else {
		cb();
	}
});

function send(text, cb) {
	fetch(url + '/write?db=chariot&precision=ms', {
		method: 'POST',
		body: text
	})
		.then(function (res) {
			if (res.status >= 200 && res.status < 300) {
				cb();
			} else {
				return res.text();
			}
		})
		.then(function (text) {
			if (text) {
				console.log(text);
			} else {
				process.stdout.write('.');
			}
		})
		.catch(function (err) {
			console.log(err);
		});
}

var express = require('express');
var path = require('path');
var bodyParser = require('body-parser');
var http = require('http');
var port = 3000;

var routes = require('./routes/index');

var app = express();

function onError(error) {
  switch (error.code) {
    case 'EACCES':
      console.error(bind + ' requires elevated privileges');
      process.exit(1);
      break;
    case 'EADDRINUSE':
      console.error(bind + ' is already in use');
      process.exit(1);
      break;
    default:
      throw error;
  }
}

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use('/', routes);

var server = http.createServer(app);
server.on('error', onError);
server.listen(port);

console.log("listening on port " + port);
module.exports = app;

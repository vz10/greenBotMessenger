'use strict';

const chalk = require('chalk');
const redis = require('redis');
const {connectionString} = require('./local_settings.js');
const SENSORS_CHANNEL = 'sensors_data';

// The sample connects to a device-specific MQTT endpoint on your IoT Hub.
var Mqtt = require('azure-iot-device-mqtt').Mqtt;
var DeviceClient = require('azure-iot-device').Client
var Message = require('azure-iot-device').Message;

var client = DeviceClient.fromConnectionString(connectionString, Mqtt);
const sub = redis.createClient()

// Print results.
function printResultFor(op) {
  return function printResult(err, res) {
    if (err) console.log(op + ' error: ' + err.toString());
    if (res) console.log(op + ' status: ' + res.constructor.name);
  };
}


// Attach a listener to receive new messages as soon as subscribe to a channel.
sub.on('message', function(channel, message) {
  // message is json string in our case so we are going to parse it.
  var message = new Message(message);
   console.log('Sending message: ' + message.getData());

  // Send the message.
  client.sendEvent(message, printResultFor('send'));
})

// Subscribe to a channel and start handling messages
sub.subscribe(SENSORS_CHANNEL)

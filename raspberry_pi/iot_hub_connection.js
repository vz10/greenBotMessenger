'use strict';

const chalk = require('chalk');
const redis = require('redis');
const {connectionString} = require('./local_settings.js');
const SENSORS_CHANNEL = 'sensors_data';
const ACTIONS_CHANNEL = 'perform_action';

// The sample connects to a device-specific MQTT endpoint on your IoT Hub.
var Mqtt = require('azure-iot-device-mqtt').Mqtt;
var DeviceClient = require('azure-iot-device').Client
var Message = require('azure-iot-device').Message;

var client = DeviceClient.fromConnectionString(connectionString, Mqtt);
const sub = redis.createClient()
const pub = redis.createClient()

function getData(request, response) {

  function directMethodResponse(err) {
    if(err) {
      console.error(chalk.red('An error ocurred when sending a method response:\n' + err.toString()));
    } else {
        console.log(chalk.green('Response to method \'' + request.methodName + '\' sent successfully.' ));
    }
  }

  console.log(chalk.green('Direct method payload received:'));
  console.log(chalk.green(request.payload));

  if (!request.payload) {
    console.log(chalk.red('Invalid payload received'));
    response.send(400, 'Invalid direct method parameter: ' + request.payload, directMethodResponse);
  } else {
    pub.publish(ACTIONS_CHANNEL, JSON.stringify({action: request.payload}));
    response.send(200, 'Performing action set: ' + request.payload, directMethodResponse);
  }
}

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

client.onDeviceMethod('PerformAction', getData);

#!/usr/bin/env python

import re
import time
import json
import redis
import serial


ser = serial.Serial("/dev/ttyACM0", 9600)  #change ACM number as found from ls /dev/tty/ACM*
ser.baudrate = 9600
redis = redis.StrictRedis(host='localhost', port=6379)
pubsub = redis.pubsub()
SENSORS_CHANNEL = 'sensors_data'


SENSORS = {
    'humidity': {
        'pattern': r'Humidity:\s+(\d+\.\d+)', 
        'callback': float
    },
    'dig_temp': {
        'pattern': r'Digital_temperature:\s+(\d+\.\d+)', 
        'callback': float
    },
    'light': {
        'pattern': r'Light:\s+(\d+)', 
        'callback': int
    },
    'soil_humidity': {
        'pattern': r'Soil Humidity:\s+(\d+)', 
        'callback': lambda value: round((1024 - float(value))/1024*100, 2)
    },
    'temp': {
        'pattern': r'Temperature:\s+(\d+)', 
        'callback': int
    },
    'sound': {
        'pattern': r'Sound:\s+(\d+)', 
        'callback': int
    }
}


# Publish to the same topic in a loop forever
while True:
    try:
        line = ser.readline().decode()
    except UnicodeDecodeError:
        time.sleep(30)
        continue

    payload = {}
    for sensor_label, sensor_dict in SENSORS.items():
        try:
            match = re.match(sensor_dict['pattern'], line)
            if match:
                payload.update({
                    'timestamp': int(round(time.time() * 1000)),
                    sensor_label: sensor_dict['callback'](match.group(1))
                })
        except Exception as e:
            continue

    if payload:
        redis.publish(SENSORS_CHANNEL, json.dumps(payload))

    time.sleep(2)

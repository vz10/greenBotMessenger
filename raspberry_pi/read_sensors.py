#!/usr/bin/env python

import re
import time
import json
import redis
import serial
from collections import defaultdict


ser = serial.Serial("/dev/ttyACM0", 9600)  #change ACM number as found from ls /dev/tty/ACM*
ser.baudrate = 9600
redis = redis.StrictRedis(host='localhost', port=6379)
pubsub = redis.pubsub()
PUBLISH_TIMEOUT = 300  # 5 mins
TIMEOUT_BETWEEN_READ = 2
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
        'callback': lambda value: round((1024 - float(value)) / 1024 * 100, 2)
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
    payload = defaultdict(list)
    for _ in range(PUBLISH_TIMEOUT / TIMEOUT_BETWEEN_READ):
        line = ser.readline().decode()
        for sensor_label, sensor_dict in SENSORS.items():
            try:
                match = re.match(sensor_dict['pattern'], line)
                if match:
                    payload[sensor_label].append(sensor_dict['callback'](match.group(1)))
            except Exception as e:
                continue

        time.sleep(TIMEOUT_BETWEEN_READ)

    sensors_data = dict(
        {label: round(sum(value)/len(value), 2) for label, value in payload.items()},
        timestamp=int(round(time.time() * 1000))
    )
    payload = defaultdict(list)
    redis.publish(SENSORS_CHANNEL, json.dumps(sensors_data))

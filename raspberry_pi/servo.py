#!/usr/bin/env python

from time import sleep
from collections import OrderedDict

import redis
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

FAN_PIN = 24  # 18
WATER_PIN = 23  # 16
LIGHT_1_PIN = 17  # 11
LIGHT_2_PIN = 27  # 13
LIGHT_3_PIN = 22  # 15
# https://pinout.xyz/
PINS = [
    FAN_PIN, WATER_PIN, 
    LIGHT_1_PIN, LIGHT_2_PIN, LIGHT_3_PIN
]
LIGHTS = OrderedDict({
    LIGHT_1_PIN: False, 
    LIGHT_2_PIN: False, 
    LIGHT_3_PIN: False
})
COMMANDS_CHANNEL = 'commands'


def on(servo):
    _rotate(servo, 45)


def off(servo):
    _rotate(servo, 0)


def _rotate(servo, angle):
    pwm = GPIO.PWM(servo, 50)
    pwm.start(2)
    pwm.ChangeDutyCycle(angle / 18. + 2.)
    sleep(.5)
    pwm.stop()


def control_light(offset):
    light_on = len(filter(lambda state: state, LIGHTS.values()))
    try:
        pin = LIGHTS.keys()[light_on + offset]
    except IndexError as e:
        pin = None

    if pin is not None:
        if offset:
            on(pin)
            LIGHTS[pin] = True
        else:
            off(pin)
            LIGHTS[pin] = False


if __name__ == '__main__':
    COMMANDS = {
        'more_temp': (off, FAN_PIN),
        'less_temp': (on, FAN_PIN),
        'more_water': (on, WATER_PIN),
        'less_water': (off, WATER_PIN),
        'more_light': (control_light, 1),
        'less_light': (control_light, 0)
    }

    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
        off(pin)

    redis = redis.StrictRedis(host='localhost', port=6379)
    pubsub = redis.pubsub()
    pubsub.subscribe(COMMANDS_CHANNEL)

    while True:
        message = pubsub.get_message()
        if message is not None and message.get('type') == 'message':
            action, argument = COMMANDS.get(message.get('data'))
            if action is not None:
                action(argument)

        sleep(2)

    GPIO.cleanup()

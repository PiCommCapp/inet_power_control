import os
import sys
import logging
import RPi.GPIO as GPIO
import time
import threading
import paho.mqtt.client as mqtt

# Define the configuration file path
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
sys.path.append(os.path.dirname(config_path))
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=config.LOG_FILE, filemode='a')

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(config.RELAY_PINS, GPIO.OUT, initial=GPIO.HIGH)  # Set all relay pins to HIGH (off)

# MQTT setup
if config.MQTT_ENABLED:
    def on_connect(client, userdata, flags, rc):
        logging.info("Connected to MQTT broker with result code " + str(rc))

    def on_message(client, userdata, msg):
        logging.info("MQTT message received: " + msg.topic + " " + str(msg.payload))

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
    client.loop_start()

try:
    logging.info('System setup complete.')
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info('Setup script terminated by user.')
finally:
    if config.MQTT_ENABLED:
        client.loop_stop()
    GPIO.cleanup()

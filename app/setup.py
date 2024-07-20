import os
import logging
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from config import LOG_FILE, MQTT_ENABLED, MQTT_BROKER, MQTT_PORT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')
logger = logging.getLogger(__name__)

def setup_gpio():
    logger.info("Setting up GPIO pins...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button
    GPIO.setup(27, GPIO.OUT)  # Relay 1
    GPIO.setup(22, GPIO.OUT)  # Relay 2
    GPIO.setup(23, GPIO.OUT)  # Relay 3
    GPIO.setup(24, GPIO.OUT)  # LED Indicator
    logger.info("GPIO pins setup completed.")

def setup_mqtt():
    if MQTT_ENABLED:
        logger.info("Setting up MQTT client...")
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info("MQTT client setup completed.")
    else:
        logger.info("MQTT is disabled in the configuration.")

def main():
    logger.info("Starting setup script...")
    setup_gpio()
    setup_mqtt()
    logger.info("Setup script completed successfully.")

if __name__ == "__main__":
    main()

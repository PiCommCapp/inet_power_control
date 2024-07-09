import os
import logging
import time
import RPi.GPIO as GPIO
import threading
import subprocess
from datetime import datetime
import paho.mqtt.client as mqtt

# Define log file location
LOG_DIR = "/home/server/log"
LOG_FILE = os.path.join(LOG_DIR, "inet_power_control.log")

# Create log directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=LOG_FILE,
                    filemode='a')

# Configuration variables
PING_COUNT = 15
FAIL_THRESHOLD = PING_COUNT // 2
TIME_BETWEEN_STEPS = {
    'initial_pause': 30,
    'modem_restart': 600,
    'router_restart': 300,
    'switch_restart': 3600
}
MQTT_ENABLED = True
MQTT_BROKER = "mqtt_broker_address"
MQTT_PORT = 1883
MQTT_TOPIC = "inet_power_control/status"

# GPIO setup
BUTTON_PIN = 17
RELAY_PINS = [27, 22, 23, 24]
INDICATOR_LED_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in RELAY_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

# MQTT setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
    else:
        logging.error("Failed to connect to MQTT broker, return code %d", rc)

def publish_mqtt_message(message):
    if MQTT_ENABLED:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        client.publish(MQTT_TOPIC, message)
        client.loop_stop()

# Function to blink LED
def blink_led(hz):
    while True:
        GPIO.output(INDICATOR_LED_PIN, GPIO.LOW)
        time.sleep(0.5 / hz)
        GPIO.output(INDICATOR_LED_PIN, GPIO.HIGH)
        time.sleep(0.5 / hz)

# Function to ping a host
def ping(host):
    response = subprocess.run(
        ['ping', '-c', str(PING_COUNT), host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return response.returncode == 0, response.stdout.decode()

# Function to check internet connectivity
def check_internet():
    google_success, google_output = ping("8.8.8.8")
    cloudflare_success, cloudflare_output = ping("1.1.1.1")
    success_count = google_output.count('bytes from') + cloudflare_output.count('bytes from')
    return success_count >= FAIL_THRESHOLD

# Reboot sequence
def reboot_sequence():
    logging.info("Starting reboot sequence")
    publish_mqtt_message("Starting reboot sequence")
    
    GPIO.output(RELAY_PINS, GPIO.HIGH)  # Turn off all devices
    blink_thread = threading.Thread(target=blink_led, args=(2,))
    blink_thread.start()

    time.sleep(TIME_BETWEEN_STEPS['initial_pause'])
    
    logging.info("Turning on WAN Modem")
    publish_mqtt_message("Turning on WAN Modem")
    GPIO.output(RELAY_PINS[0], GPIO.LOW)
    time.sleep(TIME_BETWEEN_STEPS['modem_restart'])
    
    logging.info("Turning on LAN Router")
    publish_mqtt_message("Turning on LAN Router")
    GPIO.output(RELAY_PINS[1], GPIO.LOW)
    time.sleep(TIME_BETWEEN_STEPS['router_restart'])
    
    logging.info("Turning on Network Switch")
    publish_mqtt_message("Turning on Network Switch")
    GPIO.output(RELAY_PINS[2], GPIO.LOW)
    time.sleep(TIME_BETWEEN_STEPS['switch_restart'])

    blink_thread.join()  # Stop blinking LED

    logging.info("Reboot sequence complete")
    publish_mqtt_message("Reboot sequence complete")

# Function to handle button press
def button_pressed(channel):
    logging.info("Manual intervention triggered by button press")
    publish_mqtt_message("Manual intervention triggered by button press")

    # Blink LED at 1 Hz
    blink_thread = threading.Thread(target=blink_led, args=(1,))
    blink_thread.start()
    
    reboot_sequence()
    
    blink_thread.join()

# Setup event detection for button press
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=300)

# Main loop
def main():
    fault_counter = 0

    while True:
        if check_internet():
            logging.info("Internet connection is up")
            publish_mqtt_message("Internet connection is up")
            fault_counter = 0
        else:
            logging.warning("Internet connection is down")
            publish_mqtt_message("Internet connection is down")
            fault_counter += 1

            if fault_counter >= 2:
                reboot_sequence()
                fault_counter = 0

        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script terminated by user")
    finally:
        GPIO.cleanup()

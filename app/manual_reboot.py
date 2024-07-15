import os
import sys
import logging
import RPi.GPIO as GPIO
import time
import threading

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

# Function to flash LED
def flash_led(frequency):
    while flashing:
        GPIO.output(config.RELAY_PINS[3], GPIO.LOW)
        time.sleep(1 / (2 * frequency))
        GPIO.output(config.RELAY_PINS[3], GPIO.HIGH)
        time.sleep(1 / (2 * frequency))

# Reboot sequence
def reboot_sequence():
    global flashing
    flashing = True
    led_thread = threading.Thread(target=flash_led, args=(2,))
    led_thread.start()
    
    logging.info('Reboot sequence initiated.')
    GPIO.output(config.RELAY_PINS, GPIO.HIGH)  # Turn off all devices
    time.sleep(config.REBOOT_DELAYS[0])
    GPIO.output(config.RELAY_PINS[0], GPIO.LOW)  # Turn on WAN Modem
    time.sleep(config.REBOOT_DELAYS[1])
    GPIO.output(config.RELAY_PINS[1], GPIO.LOW)  # Turn on LAN Router
    time.sleep(config.REBOOT_DELAYS[2])
    GPIO.output(config.RELAY_PINS[2], GPIO.LOW)  # Turn on Network Switch
    time.sleep(config.REBOOT_DELAYS[3])
    
    flashing = False
    led_thread.join()
    GPIO.output(config.RELAY_PINS[3], GPIO.LOW)  # LED indicator steady ON

# Manual reboot function
def manual_reboot(channel):
    logging.warning('Manual reboot triggered.')
    reboot_sequence()

# Button event detection
GPIO.add_event_detect(config.BUTTON_PIN, GPIO.FALLING, callback=manual_reboot, bouncetime=200)

try:
    logging.info('Manual reboot script running. Waiting for button press.')
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logging.info('Manual reboot script terminated by user.')
finally:
    GPIO.cleanup()

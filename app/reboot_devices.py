import RPi.GPIO as GPIO
import time
import subprocess
from threading import Thread, Event
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

# Configuration variables
LOG_FILE = '/home/server/log/inet_power_control.log'
PING_COUNT = 15
PING_THRESHOLD = 8
CHECK_INTERVAL = 60  # seconds
REBOOT_DELAY = 30  # seconds
WAN_MODEM_ON_DELAY = 600  # seconds (10 minutes)
LAN_ROUTER_ON_DELAY = 300  # seconds (5 minutes)
FINAL_WAIT_DELAY = 3600  # seconds (1 hour)
MANUAL_BUTTON_PIN = 17
RELAY_PINS = [27, 22, 23, 24]
LED_PIN = RELAY_PINS[3]

# MQTT configuration
MQTT_ENABLED = True
MQTT_BROKER = 'mqtt.example.com'
MQTT_PORT = 1883
MQTT_TOPIC_STATUS = 'inet_power_control/status'
MQTT_TOPIC_CONTROL = 'inet_power_control/control'
MQTT_CLIENT_ID = 'InetPowerControl'
MQTT_USERNAME = 'your_username'
MQTT_PASSWORD = 'your_password'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup button pin with internal pull-up resistor (Normally Open)
GPIO.setup(MANUAL_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup relay pins with initial state as HIGH (Normally Closed)
for pin in RELAY_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # Relays are active low

# Event to control LED blinking
stop_blinking_event = Event()

if MQTT_ENABLED:
    # MQTT client setup
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker.")
            client.subscribe(MQTT_TOPIC_CONTROL)
        else:
            logging.error("Failed to connect to MQTT broker, return code %d", rc)

    def on_message(client, userdata, msg):
        logging.info("Received MQTT message: %s", msg.payload.decode())
        if msg.payload.decode() == "reboot":
            logging.info("Manual reboot initiated by MQTT command.")
            reboot_sequence()
            reset_fail_count()

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    def mqtt_publish(topic, message):
        mqtt_client.publish(topic, message)
        logging.info("Published message to MQTT: %s -> %s", topic, message)
else:
    def mqtt_publish(topic, message):
        logging.info("MQTT disabled: %s -> %s", topic, message)

def blink_led(frequency):
    """
    Blink the LED at the given frequency (Hz) while the reboot sequence is running or manual intervention is needed.
    """
    period = 1.0 / frequency
    while not stop_blinking_event.is_set():
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn on LED
        time.sleep(period / 2)  # On duration
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn off LED
        time.sleep(period / 2)  # Off duration

def internet_check():
    """
    Check internet connectivity by pinging multiple sources PING_COUNT times.
    Returns True if at least one source is reachable more than PING_THRESHOLD times.
    """
    sources = ['google.com', 'cloudflare.com']
    for source in sources:
        success_count = 0
        for _ in range(PING_COUNT):
            try:
                # Ping the source
                response = subprocess.check_output(['ping', '-c', '1', source])
                success_count += 1
            except subprocess.CalledProcessError:
                continue  # Try the next ping if this one fails
        if success_count >= PING_THRESHOLD:
            return True  # Internet is up if more than half the pings succeed
    return False  # Internet is down if both sources fail more than half the pings

def reboot_sequence():
    """
    Perform the reboot sequence:
    1. Open all relays (turn off all devices).
    2. Start blinking the LED.
    3. Pause for REBOOT_DELAY.
    4. Turn on WAN Modem (relay 1).
    5. Pause for WAN_MODEM_ON_DELAY.
    6. Turn on LAN Router (relay 2).
    7. Pause for LAN_ROUTER_ON_DELAY.
    8. Turn on Network Switch (relay 3).
    9. Stop blinking the LED.
    10. Pause for FINAL_WAIT_DELAY.
    11. If internet is still down, close all relays for manual intervention.
    """
    logging.info("Starting reboot sequence.")
    mqtt_publish(MQTT_TOPIC_STATUS, "Starting reboot sequence.")
    
    # Open all relays (turn off all devices)
    GPIO.output(RELAY_PINS, GPIO.HIGH)

    # Start LED blinking in a separate thread at 2 Hz
    stop_blinking_event.clear()
    led_thread = Thread(target=blink_led, args=(2,))
    led_thread.start()
    
    logging.info("All devices turned off, waiting for %s seconds.", REBOOT_DELAY)
    mqtt_publish(MQTT_TOPIC_STATUS, "All devices turned off, waiting for {} seconds.".format(REBOOT_DELAY))
    time.sleep(REBOOT_DELAY)  # Pause for REBOOT_DELAY
    
    GPIO.output(RELAY_PINS[0], GPIO.LOW)  # Turn on WAN Modem (relay 1)
    logging.info("WAN Modem turned on, waiting for %s seconds.", WAN_MODEM_ON_DELAY)
    mqtt_publish(MQTT_TOPIC_STATUS, "WAN Modem turned on, waiting for {} seconds.".format(WAN_MODEM_ON_DELAY))
    time.sleep(WAN_MODEM_ON_DELAY)  # Pause for WAN_MODEM_ON_DELAY
    
    GPIO.output(RELAY_PINS[1], GPIO.LOW)  # Turn on LAN Router (relay 2)
    logging.info("LAN Router turned on, waiting for %s seconds.", LAN_ROUTER_ON_DELAY)
    mqtt_publish(MQTT_TOPIC_STATUS, "LAN Router turned on, waiting for {} seconds.".format(LAN_ROUTER_ON_DELAY))
    time.sleep(LAN_ROUTER_ON_DELAY)  # Pause for LAN_ROUTER_ON_DELAY
    
    GPIO.output(RELAY_PINS[2], GPIO.LOW)  # Turn on Network Switch (relay 3)
    logging.info("Network Switch turned on, waiting for %s seconds.", FINAL_WAIT_DELAY)
    mqtt_publish(MQTT_TOPIC_STATUS, "Network Switch turned on, waiting for {} seconds.".format(FINAL_WAIT_DELAY))
    time.sleep(FINAL_WAIT_DELAY)  # Pause for FINAL_WAIT_DELAY

    # Stop LED blinking
    stop_blinking_event.set()
    led_thread.join()

    if not internet_check():
        logging.warning("Internet still down after reboot sequence. Manual intervention required.")
        mqtt_publish(MQTT_TOPIC_STATUS, "Internet still down after reboot sequence. Manual intervention required.")
        GPIO.output(RELAY_PINS, GPIO.LOW)  # Close all relays for manual intervention
    else:
        logging.info("Internet connection restored after reboot sequence.")
        mqtt_publish(MQTT_TOPIC_STATUS, "Internet connection restored after reboot sequence.")

def manual_intervention():
    """
    Function to handle manual intervention state.
    The LED will blink at 1 Hz until the button is pressed to reset.
    """
    logging.warning("Manual intervention required, waiting for button press to reset.")
    mqtt_publish(MQTT_TOPIC_STATUS, "Manual intervention required, waiting for button press to reset.")
    
    stop_blinking_event.clear()
    led_thread = Thread(target=blink_led, args=(1,))
    led_thread.start()
    
    while GPIO.input(MANUAL_BUTTON_PIN) != GPIO.LOW:
        time.sleep(0.1)  # Small delay to reduce CPU usage
    
    stop_blinking_event.set()
    led_thread.join()
    logging.info("Manual intervention reset by button press.")
    mqtt_publish(MQTT_TOPIC_STATUS, "Manual intervention reset by button press.")

def reset_fail_count():
    global fail_count
    fail_count = 0
    logging.info("Failure counter reset.")
    mqtt_publish(MQTT_TOPIC_STATUS, "Failure counter reset.")

def main():
    """
    Main function to monitor internet connectivity and button press.
    Initiates the reboot sequence if the button is pressed or internet is down.
    """
    global fail_count
    fail_count = 0  # Counter for consecutive failures
    
    if MQTT_ENABLED:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    
    while True:
        if GPIO.input(MANUAL_BUTTON_PIN) == GPIO.LOW:  # Button press detected
            logging.info("Manual reboot initiated by button press.")
            mqtt_publish(MQTT_TOPIC_STATUS, "Manual reboot initiated by button press.")
            reboot_sequence()
            reset_fail_count()
        elif not internet_check():  # Internet check failed
            logging.warning("Internet connectivity check failed, initiating reboot sequence.")
            mqtt_publish(MQTT_TOPIC_STATUS, "Internet connectivity check failed, initiating reboot sequence.")
            reboot_sequence()
            fail_count += 1  # Increment failure counter
            if fail_count >= 2:
                logging.error("Failed twice, manual intervention required.")
                mqtt_publish(MQTT_TOPIC_STATUS, "Failed twice, manual intervention required.")
                manual_intervention()
                reset_fail_count()
        else:
            logging.info("Internet connectivity is up.")
            mqtt_publish(MQTT_TOPIC_STATUS, "Internet connectivity is up.")
            reset_fail_count()
        
        time.sleep(CHECK_INTERVAL)  # Check every CHECK_INTERVAL seconds

if __name__ == "__main__":
    try:
        logging.info("Starting Internet Power Control script.")
        mqtt_publish(MQTT_TOPIC_STATUS, "Starting Internet Power Control script.")
        main()
    except KeyboardInterrupt:
        logging.info("Script terminated by user.")
        GPIO.cleanup()  # Cleanup GPIO settings on exit
        logging.info("GPIO cleanup done.")
        mqtt_publish(MQTT_TOPIC_STATUS, "Script terminated by user, GPIO cleanup done.")
        if MQTT_ENABLED:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

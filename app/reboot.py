import time
import logging
import RPi.GPIO as GPIO
from config import LOG_FILE, RELAY_PINS, LED_PIN

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')
logger = logging.getLogger(__name__)

def setup_gpio():
    logger.info("Setting up GPIO for reboot sequence...")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in RELAY_PINS:
        GPIO.setup(pin, GPIO.OUT)
    GPIO.setup(LED_PIN, GPIO.OUT)
    logger.info("GPIO setup for reboot sequence completed.")

def reboot_sequence():
    logger.info("Starting reboot sequence...")
    # Blink the LED at 2 Hz to indicate reboot sequence
    led_blink(2)
    # Open all relays
    for pin in RELAY_PINS:
        GPIO.output(pin, GPIO.HIGH)
    logger.info("All relays opened. Pausing for 30 seconds...")
    time.sleep(30)

    # Close relay 1 (WAN Modem)
    GPIO.output(RELAY_PINS[0], GPIO.LOW)
    logger.info("Relay 1 (WAN Modem) closed. Pausing for 10 minutes...")
    time.sleep(600)

    # Close relay 2 (LAN Router)
    GPIO.output(RELAY_PINS[1], GPIO.LOW)
    logger.info("Relay 2 (LAN Router) closed. Pausing for 5 minutes...")
    time.sleep(300)

    # Close relay 3 (Network Switch)
    GPIO.output(RELAY_PINS[2], GPIO.LOW)
    logger.info("Relay 3 (Network Switch) closed. Resuming monitoring in 1 hour...")
    time.sleep(3600)

def led_blink(frequency):
    logger.info(f"Blinking LED at {frequency} Hz.")
    interval = 1 / (2 * frequency)
    for _ in range(int(3600 * frequency)):
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(interval)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(interval)

def main():
    logger.info("Starting reboot script...")
    setup_gpio()
    reboot_sequence()
    GPIO.cleanup()
    logger.info("Reboot sequence completed and GPIO cleanup done.")

if __name__ == "__main__":
    main()

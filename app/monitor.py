import time
import logging
import os
import RPi.GPIO as GPIO
from config import LOG_FILE, RELAY_PINS, LED_PIN

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')
logger = logging.getLogger(__name__)

def check_internet():
    logger.info("Checking internet connectivity...")
    response1 = os.system("ping -c 15 8.8.8.8 > /dev/null 2>&1")
    response2 = os.system("ping -c 15 1.1.1.1 > /dev/null 2>&1")
    if response1 != 0 and response2 != 0:
        logger.warning("Internet is down. Initiating reboot sequence...")
        exec(open("/usr/local/bin/reboot.py").read())
    else:
        logger.info("Internet connectivity is OK.")

def main():
    logger.info("Starting internet monitoring script...")
    while True:
        check_internet()
        time.sleep(900)

if __name__ == "__main__":
    main()

import logging
import RPi.GPIO as GPIO
from config import LOG_FILE, RELAY_PINS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')
logger = logging.getLogger(__name__)

def manual_reboot(channel):
    logger.info("Manual reboot initiated by button press.")
    # Run the reboot script
    exec(open("/usr/local/bin/reboot.py").read())

def setup_gpio():
    logger.info("Setting up GPIO for manual reboot...")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(17, GPIO.FALLING, callback=manual_reboot, bouncetime=200)
    logger.info("GPIO setup for manual reboot completed.")

def main():
    logger.info("Starting manual reboot script...")
    setup_gpio()
    # Keep the script running to monitor button press
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Manual reboot script terminated by user.")
    finally:
        GPIO.cleanup()
        logger.info("GPIO cleanup completed.")

if __name__ == "__main__":
    main()

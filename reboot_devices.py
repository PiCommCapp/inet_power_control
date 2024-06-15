import RPi.GPIO as GPIO
import time
import subprocess
from threading import Thread, Event

# Define GPIO pins
BUTTON_PIN = 17
RELAY_PINS = [27, 22, 23, 24]
LED_PIN = RELAY_PINS[3]

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup button pin with internal pull-up resistor (Normally Open)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup relay pins with initial state as HIGH (Normally Closed)
for pin in RELAY_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # Relays are active low

# Event to control LED blinking
stop_blinking_event = Event()

def blink_led():

    # Blink the LED at 2 Hz (2 times per second) while the reboot sequence is running.

    while not stop_blinking_event.is_set():
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn on LED
        time.sleep(0.25)  # 0.25 seconds on
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn off LED
        time.sleep(0.25)  # 0.25 seconds off

def internet_check():

    # Check internet connectivity by pinging multiple sources 15 times.
    # Returns True if at least one source is reachable more than half the time.

    sources = ['google.com', 'cloudflare.com']
    threshold = 8  # More than half of 15 pings should succeed
    for source in sources:
        success_count = 0
        for _ in range(15):
            try:
                # Ping the source
                response = subprocess.check_output(['ping', '-c', '1', source])
                success_count += 1
            except subprocess.CalledProcessError:
                continue  # Try the next ping if this one fails
        if success_count >= threshold:
            return True  # Internet is up if more than half the pings succeed
    return False  # Internet is down if both sources fail more than half the pings

def reboot_sequence():

    # Perform the reboot sequence:
    # 1. Open all relays (turn off all devices).
    # 2. Start blinking the LED.
    # 3. Pause for 30 seconds.
    # 4. Turn on WAN Modem (relay 1).
    # 5. Pause for 10 minutes.
    # 6. Turn on LAN Router (relay 2).
    # 7. Pause for 5 minutes.
    # 8. Turn on Network Switch (relay 3).
    # 9. Stop blinking the LED.
    # 10. Pause for 1 hour.
    # 11. If internet is still down, close all relays for manual intervention.

    # Open all relays (turn off all devices)
    GPIO.output(RELAY_PINS, GPIO.HIGH)

    # Start LED blinking in a separate thread
    stop_blinking_event.clear()
    led_thread = Thread(target=blink_led)
    led_thread.start()
    
    time.sleep(30)  # Pause for 30 seconds
    
    GPIO.output(RELAY_PINS[0], GPIO.LOW)  # Turn on WAN Modem (relay 1)
    time.sleep(600)  # Pause for 10 minutes
    
    GPIO.output(RELAY_PINS[1], GPIO.LOW)  # Turn on LAN Router (relay 2)
    time.sleep(300)  # Pause for 5 minutes
    
    GPIO.output(RELAY_PINS[2], GPIO.LOW)  # Turn on Network Switch (relay 3)
    time.sleep(3600)  # Pause for 1 hour

    # Stop LED blinking
    stop_blinking_event.set()
    led_thread.join()

    if not internet_check():
        GPIO.output(RELAY_PINS, GPIO.LOW)  # Close all relays for manual intervention

def main():

    # Main function to monitor internet connectivity and button press.
    # Initiates the reboot sequence if the button is pressed or internet is down.

    fail_count = 0  # Counter for consecutive failures
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW or not internet_check():
            print("Reboot sequence initiated")
            reboot_sequence()
            fail_count += 1  # Increment failure counter
            if fail_count >= 2:
                print("Failed twice, manual intervention required")
                break  # Exit the loop if failed twice
        else:
            fail_count = 0  # Reset failure counter if internet is up
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()  # Cleanup GPIO settings on exit

import RPi.GPIO as GPIO
import time
import subprocess

# Define GPIO pins
BUTTON_PIN = 17
RELAY_PINS = [27, 22, 23, 24]

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)

# Setup button pin with pull-up resistor (Normally Open)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setup relay pins with initial state as HIGH (Normally Closed)
for pin in RELAY_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)  # Relays are active low

def internet_check():

    # Check internet connectivity by pinging multiple sources.
    # Returns True if at least one source is reachable, False if both are down.

    sources = ['google.com', 'cloudflare.com']
    for source in sources:
        try:
            # Ping the source
            response = subprocess.check_output(['ping', '-c', '1', source])
            return True  # Internet is up if ping succeeds
        except subprocess.CalledProcessError:
            continue  # Try the next source if ping fails
    return False  # Internet is down if both pings fail

def reboot_sequence():

    # Perform the reboot sequence:
    # 1. Open all relays (turn off all devices).
    # 2. Pause for 30 seconds.
    # 3. Turn on WAN Modem (relay 1).
    # 4. Pause for 10 minutes.
    # 5. Turn on LAN Router (relay 2).
    # 6. Pause for 5 minutes.
    # 7. Turn on Network Switch (relay 3).
    # 8. Pause for 1 hour.
    # 9. If internet is still down, close all relays for manual intervention.

    GPIO.output(RELAY_PINS, GPIO.HIGH)  # Open all relays (turn off all devices)
    time.sleep(30)  # Pause for 30 seconds
    
    GPIO.output(RELAY_PINS[0], GPIO.LOW)  # Turn on WAN Modem (relay 1)
    time.sleep(600)  # Pause for 10 minutes
    
    GPIO.output(RELAY_PINS[1], GPIO.LOW)  # Turn on LAN Router (relay 2)
    time.sleep(300)  # Pause for 5 minutes
    
    GPIO.output(RELAY_PINS[2], GPIO.LOW)  # Turn on Network Switch (relay 3)
    time.sleep(3600)  # Pause for 1 hour

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

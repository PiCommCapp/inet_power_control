# monitor.py
import subprocess
import logging
import time
# Define the configuration file path
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
sys.path.append(os.path.dirname(config_path))
import config
from reboot import reboot_sequence

def ping(host):
    response = subprocess.run(
        ['ping', '-c', str(PING_COUNT), host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return response.returncode == 0, response.stdout.decode()

def check_internet():
    google_success, google_output = ping("8.8.8.8")
    cloudflare_success, cloudflare_output = ping("1.1.1.1")
    success_count = google_output.count('bytes from') + cloudflare_output.count('bytes from')
    return success_count >= FAIL_THRESHOLD

if __name__ == "__main__":
    fault_counter = 0
    logging.info("Starting automatic monitoring")

    while True:
        if check_internet():
            logging.info("Internet connection is up")
            fault_counter = 0
        else:
            logging.warning("Internet connection is down")
            fault_counter += 1

            if fault_counter >= 2:
                reboot_sequence()
                fault_counter = 0

        time.sleep(CHECK_INTERVAL)

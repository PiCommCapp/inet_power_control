# config.py
LOG_DIR = "/home/server/log"
LOG_FILE = f"{LOG_DIR}/inet_power_control.log"
PING_COUNT = 15
FAIL_THRESHOLD = PING_COUNT // 2
TIME_BETWEEN_STEPS = {
    'initial_pause': 30,
    'modem_restart': 600,
    'router_restart': 300,
    'switch_restart': 3600
}
MQTT_ENABLED = False
MQTT_BROKER = "mqtt_broker_address"
MQTT_PORT = 1883
MQTT_TOPIC = "inet_power_control/status"
BUTTON_PIN = 17
RELAY_PINS = [27, 22, 23, 24]
INDICATOR_LED_PIN = 24
CHECK_INTERVAL = 900  # 15 minutes

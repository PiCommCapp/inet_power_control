#!/bin/bash

# Function to check the last command's success and exit on failure
check_success() {
    if [ $? -ne 0 ]; then
        echo "Error occurred in previous command. Exiting."
        exit 1
    fi
}

# Update the package list
echo "Updating package list..."
sudo apt update
check_success

# Install required packages
echo "Installing required packages..."
sudo apt install -y python3-pip logrotate
check_success

# Install Python package
# echo "Installing Python packages..."
# pip3 install RPi.GPIO paho-mqtt
# check_success

# Define app directory and filenames
APP_DIR="$(pwd)/app"
SCRIPT_NAME="reboot_devices.py"
SERVICE_NAME="reboot_devices.service"
LOGROTATE_CONF="inet_logrotate"

# Create symlinks for the service file and the script
echo "Creating symlinks for the service file and the script..."
sudo ln -sf ${APP_DIR}/${SCRIPT_NAME} /usr/local/bin/${SCRIPT_NAME}
check_success
sudo ln -sf ${APP_DIR}/${SERVICE_NAME} /etc/systemd/system/${SERVICE_NAME}
check_success

# Configure log rotation
echo "Configuring log rotation..."
sudo ln -sf ${APP_DIR}/${LOGROTATE_CONF} /etc/logrotate.d/inet_power_control
check_success

# Set permissions for logrotate configuration
sudo chmod 644 /etc/logrotate.d/inet_power_control
check_success

# Start the service and set it to run at boot
echo "Starting the service and enabling it to run at boot..."
sudo systemctl enable ${SERVICE_NAME}
check_success
sudo systemctl start ${SERVICE_NAME}
check_success

# Check the status of the service
echo "Checking the status of the service..."
sudo systemctl status ${SERVICE_NAME}

echo "Installation complete."

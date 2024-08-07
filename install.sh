#!/bin/bash

# Function to check the last command's success and exit on failure
check_success() {
    if [ $? -ne 0 ]; then
        echo "Error occurred in the previous command. Exiting."
        exit 1
    fi
}

# Update the package list
echo "Updating package list..."
sudo apt update
check_success

# Install required packages
echo "Installing required packages..."
sudo apt install -y python3-pip python3-venv logrotate
check_success

# Define app directory and filenames
APP_DIR="$HOME/inet_power_control/app"
LOG_DIR="$HOME/inet_power_control/log"
LOG_FILE="${LOG_DIR}/inet_power_control.log"
VENV_DIR="${APP_DIR}/venv"

# Create virtual environment and install Python packages
echo "Creating virtual environment and installing Python packages..."
python3 -m venv ${VENV_DIR}
check_success

source ${VENV_DIR}/bin/activate
pip install RPi.GPIO paho-mqtt
check_success
deactivate

# Create log directory and set permissions
echo "Creating log directory and setting permissions..."
mkdir -p ${LOG_DIR}
touch ${LOG_FILE}
check_success

# Remove existing config.py if it exists and copy the new config.py
echo "Setting up configuration file..."
if [ -f ${APP_DIR}/config.py ]; then
    rm ${APP_DIR}/config.py
    check_success
fi
cp ${APP_DIR}/../config.py ${APP_DIR}/config.py
check_success

# Create symlinks for the service file and the scripts
echo "Creating symlinks for the scripts..."
sudo ln -sf ${APP_DIR}/setup.py /usr/local/bin/setup.py
sudo ln -sf ${APP_DIR}/manual_reboot.py /usr/local/bin/manual_reboot.py
sudo ln -sf ${APP_DIR}/reboot.py /usr/local/bin/reboot.py
sudo ln -sf ${APP_DIR}/monitor.py /usr/local/bin/monitor.py
check_success

# Ensure the logrotate configuration file exists before creating the symlink
echo "Checking and creating logrotate configuration..."
if [ -f ${APP_DIR}/inet_logrotate ]; then
    sudo ln -sf ${APP_DIR}/inet_logrotate /etc/logrotate.d/inet_power_control
    sudo chmod 644 /etc/logrotate.d/inet_power_control
    check_success
else
    echo "Logrotate configuration file not found. Skipping logrotate setup."
fi

# Make sure the setup script is executable
echo "Making setup script executable..."
chmod +x ${APP_DIR}/setup.py
check_success

# Run the setup script
echo "Running setup script..."
sudo ${VENV_DIR}/bin/python3 /usr/local/bin/setup.py
check_success

# Create and start the services for manual reboot and monitoring
echo "Creating and starting services..."
sudo tee /etc/systemd/system/manual_reboot.service > /dev/null <<EOF
[Unit]
Description=Manual Reboot Service
After=network.target

[Service]
ExecStart=${VENV_DIR}/bin/python3 /usr/local/bin/manual_reboot.py
WorkingDirectory=${APP_DIR}
StandardOutput=append:/var/log/manual_reboot.log
StandardError=append:/var/log/manual_reboot.err.log
Restart=always
User=server
Group=server

[Install]
WantedBy=multi-user.target
EOF
check_success

sudo tee /etc/systemd/system/monitor.service > /dev/null <<EOF
[Unit]
Description=Internet Monitoring Service
After=network.target

[Service]
ExecStart=${VENV_DIR}/bin/python3 /usr/local/bin/monitor.py
WorkingDirectory=${APP_DIR}
StandardOutput=append:/var/log/monitor.log
StandardError=append:/var/log/monitor.err.log
Restart=always
User=server
Group=server

[Install]
WantedBy=multi-user.target
EOF
check_success

# Enable and start the services
echo "Enabling and starting services..."
sudo systemctl enable manual_reboot.service
check_success
sudo systemctl start manual_reboot.service
check_success
sudo systemctl enable monitor.service
check_success
sudo systemctl start monitor.service
check_success

# Check the status of the services
echo "Checking the status of the services..."
sudo systemctl status manual_reboot.service
sudo systemctl status monitor.service

# Verify installation
if systemctl is-active --quiet manual_reboot.service && systemctl is-active --quiet monitor.service; then
    echo "Installation and setup completed successfully."
else
    echo "There was an issue with the installation. Please check the logs for more details."
    exit 1
fi

echo "Installation complete."

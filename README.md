# Internet Power Control 

A Raspberry Pi based power control system to reboot devices automatically at internet loss. It can also be rebooted with a button.

The RPi pings Google and Cloudflare and if both are down it initiates a reboot sequence.

## Hardware

The system has a RPi, a 4 relay daughter board, and a power supply as all my devices are 12Vdc. The RPi is wired to the daughter board as follows;

| Channel | GPIO | Pin | Resistor  | Controlled Device | Condition       |
|---------|------|-----|-----------|-------------------|-----------------|
| button  | 17   | 11  | Pull Up   | Manual Reboot     | Normally Open   |
| 1       | 27   | 13  | Pull Down | WAN Modem         | Normally Closed |
| 2       | 22   | 15  | Pull Down | LAN Router        | Normally Closed |
| 3       | 23   | 16  | Pull Down | Network Switch    | Normally Closed |
| 4       | 24   | 18  | Pull Down | not used          | Normally Closed |

## Reboot Sequence

1. Open all relays (turn off all devices).
2. Pause for 30 seconds.
3. Turn on WAN Modem (relay 1).
4. Pause for 10 minutes.
5. Turn on LAN Router (relay 2).
6. Pause for 5 minutes.
7. Turn on Network Switch (relay 3).
8. Pause for 1 hour.
9. If internet is still down, close all relays for manual intervention.

## Installation

This is assuming you have an operational RPi with RPiOS lite installed. The pi should also be connected to the internet.

Install prerequisites

```bash
sudo apt update
sudo apt install python3-pip
pip3 install RPi.GPIO
```

Clone the repository to your home directory and change into the directory;

```bash
cd ~
git clone https://github.com/PiCommCapp/inet_power_control
cd inet_power_control
```

Then create a symlink for the service file and the script

```bash
ln -s ./reboot_devices.py /bin/reboot_devices.py
ln -s ./reboot_device.service /etc/systemd/system/reboot_devices.service
```

Then start the service and set to run at boot

```bash
sudo systemctl enable reboot_devices.service
sudo systemctl start reboot_devices.service
```

You can then check the service is running correctly

```bash
sudo systemctl status reboot_devices.service
```

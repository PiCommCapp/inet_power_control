# Internet Power Control

A Raspberry Pi-based power control system to automatically reboot devices when internet connectivity is lost. The system can also be manually rebooted using a button.

The Raspberry Pi pings Google and Cloudflare, and if both are unreachable, it initiates a reboot sequence.

There is the added benefit that i will put in a single power supply to power all the devices, clearing two outlets!

## Network

The network being controlled consists of three critical devices:

1. Modem
2. Router/Firewall
3. Network Switch

All these devices in this setup use 12V DC power. This can be modified for other voltages, but that is up to you!

## Hardware

The system consists of a [Raspberry Pi](https://www.raspberrypi.com/), a [4-relay board](), and a [power supply]() (as all devices use 12V DC). The Raspberry Pi is wired to the relay board as follows:

| Channel | GPIO | Pin | Resistor  | Controlled Device | Condition       |
|---------|------|-----|-----------|-------------------|-----------------|
| button  | 17   | 11  | Pull Up   | Manual Reboot     | Normally Open   |
| 1       | 27   | 13  | Pull Down | WAN Modem         | Normally Closed |
| 2       | 22   | 15  | Pull Down | LAN Router        | Normally Closed |
| 3       | 23   | 16  | Pull Down | Network Switch    | Normally Closed |
| 4       | 24   | 18  | Pull Down | Indicator LED     | Normally Closed |

The button is connected to ground.

### Indicator States

| Output | State | Description           |
|--------|-------|-----------------------|
| RLY 4  | On    | System running        |
|        | Off   | System not powered    |
|        | 1 Hz  | Intervention Required |
|        | 2 Hz  | System rebooting      |

## Reboot Sequence

1. Open all relays (turn off all devices).
2. Pause for 30 seconds.
3. Turn on the WAN Modem (relay 1).
4. Pause for 10 minutes.
5. Turn on the LAN Router (relay 2).
6. Pause for 5 minutes.
7. Turn on the Network Switch (relay 3).
8. Pause for 1 hour.
9. If the internet is still down, close all relays for manual intervention.

## Installation

This assumes you have an operational Raspberry Pi with Raspberry Pi OS Lite installed. The Pi should also be connected to the internet.

Clone the repository to your home directory and change into the directory:

```bash
cd ~
git clone https://github.com/PiCommCapp/inet_power_control
cd inet_power_control
./install.sh
```

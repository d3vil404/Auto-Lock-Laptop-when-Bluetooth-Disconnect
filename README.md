# Auto-Lock-Laptop-when-Bluetooth-Disconnect
its a Python tool designed to give security, if your mobile connected to laptop bluetooth is do nothing but once its disconnect  suddenly your laptop will lock , then u need to type password  to unlock your laptop. its works without root also , you can also make a auto start service who start automatically when the laptop in turned on . 



# Bluetooth Device Connection Monitor

A Python tool for monitoring Bluetooth device connections on Linux systems. It tracks Bluetooth device connections and disconnections in real-time, and can automatically trigger a screen lock when a specific device disconnects.

## Features

- Real-time monitoring of Bluetooth device connections/disconnections
- Support for monitoring specific devices or all Bluetooth devices
- Automatic screen locking when a designated device disconnects
- Configurable lock delay
- Customizable lock script
- Device name resolution for better readability
- Dual monitoring (event-based + periodic checks for reliability)

## Prerequisites

### System Requirements
- Linux system with Bluetooth support
- Python 3.6 or higher
- BlueZ Bluetooth stack
- Wayland or X11 display server (for screen locking)

### Required Packages

Install the necessary packages:

**For Debian/Ubuntu/Kali Linux:**
```bash
sudo apt update
sudo apt install python3 bluez bluez-tools

For screen locking (choose one):

Wayland (swaylock):
bash

sudo apt install swaylock

X11 (i3lock, slock, etc.):
bash

sudo apt install i3lock
# or
sudo apt install slock

Installation

    Download the script:

bash

git clone <repository-url>
cd bluetooth-monitor

    Make the Python script executable:

bash

chmod +x bluetooth_monitor.py

    Create the lock script:
    Create a file named lock_screen.sh with the following content:

bash

#!/bin/bash
USER_NAME="your_username"

if [ "$EUID" -eq 0 ]; then
    echo "⚠ Cannot lock screen from root in Wayland."
    echo "Run this script as $USER_NAME to lock the screen."
    exit 1
else
    # For Wayland (sway/wlroots)
    swaylock -f -c 000000
    
    # For X11 (uncomment one of the below)
    # i3lock -c 000000
    # slock
    # dm-tool lock
fi

    Make the lock script executable:

bash

chmod +x lock_screen.sh

    Edit the lock script:
    Replace "your_username" with your actual username in the lock_screen.sh file.

Usage
Basic Commands

Monitor all Bluetooth devices:
bash

python3 bluetooth_monitor.py

Monitor specific device by MAC address:
bash

python3 bluetooth_monitor.py --mac AA:BB:CC:11:22:33

Auto-lock when specific device disconnects:
bash

python3 bluetooth_monitor.py --lock-mac AA:BB:CC:11:22:33

Combine monitoring and auto-lock for same device:
bash

python3 bluetooth_monitor.py --mac AA:BB:CC:11:22:33 --lock-mac AA:BB:CC:11:22:33

Custom lock delay (10 seconds):
bash

python3 bluetooth_monitor.py --lock-mac AA:BB:CC:11:22:33 --lock-delay 10

Use custom lock script:
bash

python3 bluetooth_monitor.py --lock-mac AA:BB:CC:11:22:33 --lock-script /path/to/your/lock_script.sh

Command Line Options
Option	Description	Default
--mac	Filter events for specific MAC address	All devices
--lock-mac	MAC address that triggers screen lock when disconnected	None
--lock-delay	Delay in seconds before locking screen	5
--lock-script	Path to lock script	lock_screen.sh
Finding Your Device MAC Address

    Connect your Bluetooth device first

    Run bluetoothctl to find MAC:

bash

bluetoothctl devices Connected

    Or list all paired devices:

bash

bluetoothctl devices

Example output:
text

Device AA:BB:CC:11:22:33 Wireless Headphones
Device DD:EE:FF:44:55:66 Magic Mouse

Examples

Example 1: Monitor headphones and lock screen when they disconnect
bash

python3 bluetooth_monitor.py --mac 5C:A0:6C:16:8A:24 --lock-mac 5C:A0:6C:16:8A:24 --lock-delay 3

Example 2: Monitor all devices but only lock when mouse disconnects
bash

python3 bluetooth_monitor.py --lock-mac DD:EE:FF:44:55:66

Example 3: Quick lock (2 seconds delay) for security
bash

python3 bluetooth_monitor.py --lock-mac AA:BB:CC:11:22:33 --lock-delay 2

Output Format

The tool provides real-time output with timestamps:
text

[2024-01-15 10:30:45] INITIAL      AA:BB:CC:11:22:33  Wireless Headphones
[2024-01-15 10:31:22] DISCONNECTED AA:BB:CC:11:22:33  Wireless Headphones
[2024-01-15 10:31:22] Lock script scheduled in 5 seconds
[2024-01-15 10:31:27] Running lock script: lock_screen.sh
[2024-01-15 10:31:27] Lock script executed successfully

Customizing Lock Behavior
For Different Desktop Environments

GNOME (Wayland):
bash

#!/bin/bash
loginctl lock-session

KDE Plasma:
bash

#!/bin/bash
qdbus org.kde.screensaver /ScreenSaver Lock

Xfce:
bash

#!/bin/bash
xflock4

Custom i3lock with image:
bash

#!/bin/bash
i3lock -i /path/to/wallpaper.png -t

Running as Service

To run automatically on startup:

    Create systemd service file:

bash

sudo nano /etc/systemd/system/bluetooth-monitor.service

    Add service configuration:

ini

[Unit]
Description=Bluetooth Monitor Service
After=bluetooth.service
Wants=bluetooth.service

[Service]
Type=simple
User=your_username
ExecStart=/path/to/bluetooth_monitor.py --lock-mac AA:BB:CC:11:22:33
WorkingDirectory=/path/to/script/directory
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

    Enable and start service:

bash

sudo systemctl daemon-reload
sudo systemctl enable bluetooth-monitor.service
sudo systemctl start bluetooth-monitor.service

Troubleshooting
Common Issues

    "bluetoothctl not found"
    bash

sudo apt install bluez bluez-tools

"Cannot lock screen from root"

    Ensure the lock script runs as your user, not root

    Check the USER_NAME in lock_screen.sh matches your username

Lock script not executing
bash

chmod +x lock_screen.sh
ls -la lock_screen.sh  # Should show executable permissions

Bluetooth device not detected
bash

sudo systemctl restart bluetooth
bluetoothctl scan on  # Wait for devices to appear

Permission denied errors
bash

# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER
newgrp bluetooth

Debug Mode

For troubleshooting, you can modify the Python script to add debug output or run with verbose logging.
Security Considerations

    The tool requires Bluetooth access but doesn't need root privileges for basic monitoring

    Lock script should be owned by and executable only by your user

    Consider using a shorter lock delay for sensitive environments

    The tool doesn't store any sensitive information

Files

    bluetooth_monitor.py - Main monitoring script

    lock_screen.sh - Screen lock script (customizable)

    README.md - This documentation file

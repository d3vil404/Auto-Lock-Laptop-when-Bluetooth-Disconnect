#!/bin/bash
USER_NAME="veronica"

if [ "$EUID" -eq 0 ]; then
    echo "⚠ Cannot lock screen from root in Wayland."
    echo "Run this script as $USER_NAME to lock the screen."
    exit 1
else
    swaylock -f -c 000000
fi

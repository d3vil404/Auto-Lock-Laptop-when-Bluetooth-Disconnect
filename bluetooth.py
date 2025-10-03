#!/usr/bin/env python3
"""
Bluetooth device connection monitor for Linux.
Monitors Bluetooth devices and prints connect/disconnect events in real time.
Runs a lock script when specific device disconnects.
"""

import sys
import time
import argparse
import subprocess
import threading
import os
from datetime import datetime
from collections import defaultdict


class BluetoothMonitor:
    def __init__(self, target_mac=None, lock_mac=None, lock_delay=5, lock_script="lock_screen.sh"):
        self.target_mac = target_mac.upper() if target_mac else None
        self.lock_mac = lock_mac.upper() if lock_mac else None
        self.lock_delay = lock_delay
        self.lock_script = lock_script
        self.connected_devices = set()
        self.device_names = {}
        self.running = True
        self.lock_timer = None
        
    def run_lock_script(self):
        """Run the lock script in background."""
        try:
            print(f"[{self.get_timestamp()}] Running lock script: {self.lock_script}")
            
            # Check if lock script exists and is executable
            if os.path.exists(self.lock_script) and os.access(self.lock_script, os.X_OK):
                # Run the script in background
                subprocess.Popen([f'./{self.lock_script}'], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print(f"[{self.get_timestamp()}] Lock script executed successfully")
            else:
                print(f"[{self.get_timestamp()}] ERROR: Lock script {self.lock_script} not found or not executable")
                print(f"[{self.get_timestamp()}] Please create {self.lock_script} with your lock commands")
                
        except Exception as e:
            print(f"[{self.get_timestamp()}] ERROR: Failed to run lock script: {e}")

    def schedule_lock(self):
        """Schedule lock script execution after delay."""
        if self.lock_timer and self.lock_timer.is_alive():
            self.lock_timer.cancel()
            
        self.lock_timer = threading.Timer(self.lock_delay, self.run_lock_script)
        self.lock_timer.daemon = True
        self.lock_timer.start()
        print(f"[{self.get_timestamp()}] Lock script scheduled in {self.lock_delay} seconds")

    def cancel_lock(self):
        """Cancel scheduled lock script execution."""
        if self.lock_timer and self.lock_timer.is_alive():
            self.lock_timer.cancel()
            print(f"[{self.get_timestamp()}] Lock script execution cancelled")

    def get_device_name(self, mac):
        """Get friendly name for a Bluetooth device."""
        if mac in self.device_names:
            return self.device_names[mac]
            
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', mac],
                capture_output=True, text=True, timeout=2
            )
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Name:'):
                    name = line.split('Name:', 1)[1].strip()
                    self.device_names[mac] = name
                    return name
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
            
        self.device_names[mac] = mac
        return mac

    def parse_devices(self, output):
        """Parse connected devices from bluetoothctl output."""
        devices = set()
        current_mac = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            # Look for device MAC address
            if line.startswith('Device '):
                parts = line.split()
                if len(parts) >= 2:
                    current_mac = parts[1].upper()
            
            # Check if device is connected
            elif current_mac and 'Connected: yes' in line:
                if not self.target_mac or current_mac == self.target_mac:
                    devices.add(current_mac)
                current_mac = None
            elif current_mac and ('Connected: no' in line or 'Paired:' in line):
                current_mac = None
                
        return devices

    def get_connected_devices(self):
        """Get currently connected Bluetooth devices."""
        try:
            result = subprocess.run(
                ['bluetoothctl', 'devices', 'Connected'],
                capture_output=True, text=True, timeout=5
            )
            devices = set()
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Device '):
                    parts = line.split()
                    if len(parts) >= 2:
                        mac = parts[1].upper()
                        if not self.target_mac or mac == self.target_mac:
                            devices.add(mac)
            return devices
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            print(f"[{self.get_timestamp()}] ERROR: Failed to get devices: {e}")
            return set()

    def get_timestamp(self):
        """Get current timestamp for logging."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def monitor_events(self):
        """Monitor Bluetooth events using bluetoothctl."""
        try:
            process = subprocess.Popen(
                ['bluetoothctl', '--monitor'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if not line:
                    break
                    
                self.process_event_line(line.strip())
                
        except Exception as e:
            print(f"[{self.get_timestamp()}] ERROR: Event monitoring failed: {e}")
        finally:
            if hasattr(self, 'process'):
                process.terminate()

    def process_event_line(self, line):
        """Process a single event line from bluetoothctl monitor."""
        if not line:
            return
            
        mac = None
        event_type = None
        
        # Look for connection events
        if 'Connected: yes' in line:
            event_type = 'CONNECTED'
            # Extract MAC from the line
            if 'Device ' in line:
                parts = line.split()
                for part in parts:
                    if ':' in part and len(part) == 17:
                        mac = part.upper()
                        break
        elif 'Connected: no' in line:
            event_type = 'DISCONNECTED'
            # Extract MAC from the line
            if 'Device ' in line:
                parts = line.split()
                for part in parts:
                    if ':' in part and len(part) == 17:
                        mac = part.upper()
                        break
        
        if mac and event_type:
            name = self.get_device_name(mac)
            
            if event_type == 'CONNECTED' and mac not in self.connected_devices:
                self.connected_devices.add(mac)
                print(f"[{self.get_timestamp()}] CONNECTED    {mac}  {name}")
                
                # Handle lock device reconnection
                if self.lock_mac and mac == self.lock_mac:
                    self.cancel_lock()
                    
            elif event_type == 'DISCONNECTED' and mac in self.connected_devices:
                self.connected_devices.discard(mac)
                print(f"[{self.get_timestamp()}] DISCONNECTED {mac}  {name}")
                
                # Handle lock device disconnection
                if self.lock_mac and mac == self.lock_mac:
                    self.schedule_lock()

    def periodic_check(self):
        """Periodically check device status as backup."""
        while self.running:
            time.sleep(5)  # Check every 5 seconds
            try:
                current_devices = self.get_connected_devices()
                
                # Check for new connections
                for mac in current_devices - self.connected_devices:
                    name = self.get_device_name(mac)
                    self.connected_devices.add(mac)
                    print(f"[{self.get_timestamp()}] CONNECTED    {mac}  {name}")
                    
                    # Handle lock device reconnection
                    if self.lock_mac and mac == self.lock_mac:
                        self.cancel_lock()
                
                # Check for disconnections
                for mac in self.connected_devices - current_devices:
                    name = self.device_names.get(mac, mac)
                    self.connected_devices.discard(mac)
                    print(f"[{self.get_timestamp()}] DISCONNECTED {mac}  {name}")
                    
                    # Handle lock device disconnection
                    if self.lock_mac and mac == self.lock_mac:
                        self.schedule_lock()
                        
            except Exception as e:
                print(f"[{self.get_timestamp()}] ERROR: Periodic check failed: {e}")

    def run(self):
        """Start the Bluetooth monitor."""
        print(f"[{self.get_timestamp()}] Starting Bluetooth monitor...")
        if self.target_mac:
            print(f"[{self.get_timestamp()}] Filtering for device: {self.target_mac}")
        else:
            print(f"[{self.get_timestamp()}] Monitoring all Bluetooth devices")
        
        if self.lock_mac:
            print(f"[{self.get_timestamp()}] Auto-lock enabled for: {self.lock_mac} (delay: {self.lock_delay}s)")
            print(f"[{self.get_timestamp()}] Using lock script: {self.lock_script}")
            
            # Check if lock script exists
            if not os.path.exists(self.lock_script):
                print(f"[{self.get_timestamp()}] WARNING: Lock script {self.lock_script} not found")
                print(f"[{self.get_timestamp()}] Create {self.lock_script} with your screen lock command")
        
        # Get initial state
        try:
            self.connected_devices = self.get_connected_devices()
            for mac in self.connected_devices:
                name = self.get_device_name(mac)
                print(f"[{self.get_timestamp()}] INITIAL      {mac}  {name}")
                
                # If lock device is initially disconnected, schedule lock
                if self.lock_mac and self.lock_mac not in self.connected_devices:
                    self.schedule_lock()
                    
        except Exception as e:
            print(f"[{self.get_timestamp()}] ERROR: Failed to get initial state: {e}")
        
        # Start event monitoring in separate thread
        event_thread = threading.Thread(target=self.monitor_events, daemon=True)
        event_thread.start()
        
        # Start periodic checking in separate thread
        check_thread = threading.Thread(target=self.periodic_check, daemon=True)
        check_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
                # Check if event thread is still alive
                if not event_thread.is_alive():
                    print(f"[{self.get_timestamp()}] WARNING: Event thread died, restarting...")
                    event_thread = threading.Thread(target=self.monitor_events, daemon=True)
                    event_thread.start()
                    
        except KeyboardInterrupt:
            print(f"\n[{self.get_timestamp()}] Stopping monitor...")
        finally:
            self.running = False
            self.cancel_lock()


def main():
    parser = argparse.ArgumentParser(description='Monitor Bluetooth device connections')
    parser.add_argument('--mac', help='Filter events for specific MAC address (e.g., AA:BB:CC:11:22:33)')
    parser.add_argument('--lock-mac', help='MAC address that triggers screen lock when disconnected (e.g., 5C:A0:6C:16:8A:24)')
    parser.add_argument('--lock-delay', type=int, default=5, help='Delay in seconds before locking screen (default: 5)')
    parser.add_argument('--lock-script', default='lock_screen.sh', help='Path to lock script (default: lock_screen.sh)')
    
    args = parser.parse_args()
    
    # Validate MAC format if provided
    def validate_mac(mac_str, param_name):
        if mac_str:
            mac = mac_str.upper().replace('-', ':')
            if len(mac) != 17 or mac.count(':') != 5:
                print(f"ERROR: Invalid MAC address format for {param_name}. Use AA:BB:CC:11:22:33")
                sys.exit(1)
            return mac
        return None
    
    target_mac = validate_mac(args.mac, "--mac")
    lock_mac = validate_mac(args.lock_mac, "--lock-mac")
    
    # Check if bluetoothctl is available
    try:
        subprocess.run(['bluetoothctl', '--version'], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: bluetoothctl not found. Please install bluez package.")
        sys.exit(1)
    
    monitor = BluetoothMonitor(
        target_mac=target_mac, 
        lock_mac=lock_mac, 
        lock_delay=args.lock_delay,
        lock_script=args.lock_script
    )
    monitor.run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
ESP32 Gyro Steering Controller for Live for Speed
Receives gyro data from ESP32 via UDP and converts to Xbox controller input
"""

import socket
import sys
import time
import math
from collections import deque

try:
    import vgamepad as vg
except Exception as e:
    print("Missing vgamepad. Install with: pip install vgamepad")
    raise e

# Configuration constants
UDP_IP = "0.0.0.0"  # Listen on all network interfaces
UDP_PORT = 5555     # Default port
STEERING_SENSITIVITY = 2.0  # Multiplier for gyro to steering conversion
STEERING_DEADZONE = 5       # Degrees - ignore small movements
MAX_STEERING_ANGLE = 45     # Degrees - maximum steering angle
BUFFER_SIZE = 5             # Number of samples for smoothing
SMOOTHING_ALPHA = 0.7       # Exponential smoothing factor (0-1)

class GyroSteeringController:
    def __init__(self, udp_ip=UDP_IP, udp_port=UDP_PORT):
        # Virtual gamepad
        self.gamepad = vg.VX360Gamepad()
        
        # UDP socket setup
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.sock = None
        
        # Steering state
        self.steering_buffer = deque(maxlen=BUFFER_SIZE)
        self.smoothed_steering = 0.0
        self.last_data_time = time.time()
        
        # Calibration
        self.calibration_offset = 0.0
        self.is_calibrated = False
        
        # Statistics
        self.packet_count = 0
        self.last_status_time = time.time()
        
        self.setup_socket()
    
    def setup_socket(self):
        """Initialize UDP socket"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.udp_ip, self.udp_port))
            self.sock.settimeout(0.1)  # 100ms timeout for responsive control
            print(f"✓ Listening for ESP32 data on {self.udp_ip}:{self.udp_port}")
        except Exception as e:
            print(f"❌ Error creating socket: {e}")
            raise
    
    def get_local_ip_addresses(self):
        """Get all local IP addresses"""
        ip_addresses = []
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            ip_addresses = [ip for ip in ip_list if not ip.startswith("127.")]
        except Exception as e:
            print(f"Could not determine IP addresses: {e}")
        return ip_addresses
    
    def parse_gyro_data(self, message):
        """Parse ESP32 gyro data in format X:val|Y:val|Z:val"""
        try:
            parts = message.split('|')
            roll = int(parts[0].split(':')[1])   # X - Roll (steering)
            pitch = int(parts[1].split(':')[1])  # Y - Pitch (not used)
            yaw = int(parts[2].split(':')[1])    # Z - Yaw (not used)
            return roll, pitch, yaw
        except (IndexError, ValueError) as e:
            print(f"Error parsing gyro data: {message} ({e})")
            return None, None, None
    
    def calibrate_steering(self, roll_value):
        """Calibrate the neutral steering position"""
        if not self.is_calibrated:
            self.calibration_offset = roll_value
            self.is_calibrated = True
            print(f"🎯 Steering calibrated! Neutral position: {roll_value}°")
            return True
        return False
    
    def calculate_steering(self, roll_value):
        """Convert gyro roll to steering value (-1.0 to 1.0)"""
        if not self.is_calibrated:
            return 0.0
        
        # Apply calibration offset
        adjusted_roll = roll_value - self.calibration_offset
        
        # Apply deadzone
        if abs(adjusted_roll) < STEERING_DEADZONE:
            adjusted_roll = 0.0
        
        # Clamp to maximum angle
        adjusted_roll = max(-MAX_STEERING_ANGLE, min(MAX_STEERING_ANGLE, adjusted_roll))
        
        # Convert to steering value (-1.0 to 1.0)
        steering = (adjusted_roll / MAX_STEERING_ANGLE) * STEERING_SENSITIVITY
        steering = max(-1.0, min(1.0, steering))
        
        return steering
    
    def apply_smoothing(self, new_steering):
        """Apply exponential smoothing to steering"""
        self.smoothed_steering = (SMOOTHING_ALPHA * new_steering + 
                                 (1 - SMOOTHING_ALPHA) * self.smoothed_steering)
        return self.smoothed_steering
    
    def send_steering_to_gamepad(self, steering_value):
        """Send steering value to virtual Xbox controller"""
        try:
            # Only steering for now - no throttle/brake
            self.gamepad.left_joystick_float(steering_value, 0.0)
            self.gamepad.update()
        except Exception as e:
            print(f"Error sending to gamepad: {e}")
    
    def display_status(self, roll, pitch, yaw, steering):
        """Display current status"""
        status_line = (f"[{self.packet_count:06d}] "
                      f"Roll: {roll:4d}° | "
                      f"Steering: {steering:+.3f} | "
                      f"Calibrated: {'✓' if self.is_calibrated else '✗'}")
        
        # Clear line and print status
        print(f"\r{status_line}", end="", flush=True)
    
    def run(self):
        """Main control loop"""
        print("=" * 70)
        print("  ESP32 Gyro Steering Controller for Live for Speed")
        print("=" * 70)
        
        # Display network info
        local_ips = self.get_local_ip_addresses()
        print("\n📍 Your Computer's IP Addresses:")
        if local_ips:
            for idx, ip in enumerate(local_ips, 1):
                print(f"   {idx}. {ip}")
        
        print(f"\n✓ Listening on {self.udp_ip}:{self.udp_port}")
        print("\n📱 ESP32 Configuration:")
        print("  1. Connect to 'SteerSetup_XXXX' WiFi network")
        print("  2. Enter one of the IP addresses above")
        print(f"  3. Enter UDP port: {self.udp_port}")
        print("  4. Save and wait for connection")
        
        print("\n🎮 Controls:")
        print("  - Tilt steering wheel left/right to steer")
        print("  - Press 'c' to calibrate neutral position")
        print("  - Press 'q' to quit")
        print("  - Ctrl+C to exit")
        
        print("\n" + "=" * 70)
        print("⏳ Waiting for ESP32 data...")
        
        try:
            while True:
                try:
                    # Receive UDP data
                    data, addr = self.sock.recvfrom(1024)
                    self.packet_count += 1
                    self.last_data_time = time.time()
                    
                    # Parse gyro data
                    message = data.decode('utf-8').strip()
                    roll, pitch, yaw = self.parse_gyro_data(message)
                    
                    if roll is not None:
                        # Auto-calibrate on first packet
                        if not self.is_calibrated:
                            self.calibrate_steering(roll)
                        
                        # Calculate steering
                        raw_steering = self.calculate_steering(roll)
                        smoothed_steering = self.apply_smoothing(raw_steering)
                        
                        # Send to gamepad
                        self.send_steering_to_gamepad(smoothed_steering)
                        
                        # Display status
                        self.display_status(roll, pitch, yaw, smoothed_steering)
                
                except socket.timeout:
                    # Check for connection loss
                    current_time = time.time()
                    if current_time - self.last_data_time > 2.0:
                        # No data for 2 seconds - center steering
                        self.send_steering_to_gamepad(0.0)
                        
                        if current_time - self.last_status_time > 5.0:
                            print(f"\n[Status] No data received. Packets: {self.packet_count}")
                            self.last_status_time = current_time
                    continue
                
                except KeyboardInterrupt:
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("\n\n🛑 Shutting down...")
        
        # Center steering and release controls
        if self.gamepad:
            self.gamepad.left_joystick_float(0.0, 0.0)
            self.gamepad.right_trigger_float(0.0)
            self.gamepad.left_trigger_float(0.0)
            self.gamepad.update()
        
        # Close socket
        if self.sock:
            self.sock.close()
        
        print(f"📊 Total packets received: {self.packet_count}")
        print("✓ Cleanup complete")

def main():
    """Main entry point"""
    # Parse command line arguments
    udp_ip = UDP_IP
    udp_port = UDP_PORT
    
    if len(sys.argv) > 1:
        try:
            udp_port = int(sys.argv[1])
        except ValueError:
            udp_ip = sys.argv[1]
            if len(sys.argv) > 2:
                try:
                    udp_port = int(sys.argv[2])
                except ValueError:
                    print(f"Invalid port: {sys.argv[2]}")
                    return 1
    
    try:
        controller = GyroSteeringController(udp_ip, udp_port)
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

def main():
    """Main entry point"""
    try:
        controller = HandGestureController()
        controller.run()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())

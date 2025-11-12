#!/usr/bin/env python3
"""
ESP32 Gyro Steering Controller for Live for Speed
Receives gyro data from ESP32 via UDP and converts to Xbox controller input
"""

import socket
import sys
import time
import math
import json
from collections import deque

try:
    import vgamepad as vg
except Exception as e:
    print("Missing vgamepad. Install with: pip install vgamepad")
    raise e

try:
    import pydirectinput
except Exception as e:
    print("Missing pydirectinput. Install with: pip install pydirectinput")
    raise e

# Configuration constants
UDP_IP = "0.0.0.0"  # Listen on all network interfaces
UDP_PORT = 5555     # Default port
STEERING_DEADZONE = 5       # Degrees - ignore small movements
MAX_STEERING_ANGLE = 90     # Degrees - ESP32 sends -90 to +90
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
        
        # Gear state
        self.current_gear = 0
        self.last_gear_shift_time = 0.0
        self.gear_shift_cooldown = 0.2  # 200ms cooldown between gear shifts
        
        # Control state
        self.last_accel = False
        self.last_brake = False
        
        # Statistics
        self.packet_count = 0
        self.last_status_time = time.time()
        self.last_debug_time = time.time()
        
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
    
    def parse_control_data(self, message):
        """Parse ESP32 control data in JSON format"""
        try:
            # Try JSON parsing first
            data = json.loads(message)
            
            # Extract steering values
            steering = data.get("steering", {})
            x = steering.get("x", 0.0)
            y = steering.get("y", 0.0)
            z = steering.get("z", 0.0)  # This is our yaw/steering value
            
            # Extract control values
            gear = data.get("gear", 0)
            accel = data.get("accel", False)
            brake = data.get("brake", False)
            
            return x, y, z, gear, accel, brake
            
        except json.JSONDecodeError:
            # Fallback to old format for backward compatibility
            try:
                parts = message.split('|')
                roll = int(parts[0].split(':')[1])   # X - Roll (not used)
                pitch = int(parts[1].split(':')[1])  # Y - Pitch (not used)
                yaw = int(parts[2].split(':')[1])    # Z - Yaw (steering)
                return roll, pitch, yaw, 0, False, False
            except (IndexError, ValueError) as e:
                print(f"Error parsing control data: {message} ({e})")
                return None, None, None, None, None, None
        except Exception as e:
            print(f"Error parsing JSON data: {message} ({e})")
            return None, None, None, None, None, None
    
    def calculate_steering(self, yaw_value):
        """Convert gyro yaw to steering value (-1.0 to 1.0)"""
        # ESP32 sends -90 to +90, map directly to -1.0 to +1.0
        # Apply deadzone
        if abs(yaw_value) < STEERING_DEADZONE:
            yaw_value = 0.0
        
        # Clamp to expected range (-90 to +90)
        clamped_yaw = max(-MAX_STEERING_ANGLE, min(MAX_STEERING_ANGLE, yaw_value))
        
        # Convert directly: -90 -> -1.0, +90 -> +1.0
        steering = clamped_yaw / MAX_STEERING_ANGLE
        
        return steering
    
    def apply_smoothing(self, new_steering):
        """Apply exponential smoothing to steering"""
        self.smoothed_steering = (SMOOTHING_ALPHA * new_steering + 
                                 (1 - SMOOTHING_ALPHA) * self.smoothed_steering)
        return self.smoothed_steering
    
    def handle_gear_shift(self, new_gear):
        """Handle gear shifting with keyboard controls and cooldown"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_gear_shift_time < self.gear_shift_cooldown:
            return
        
        # Compare with current gear
        if new_gear > self.current_gear:
            # Shift up - press 's'
            pydirectinput.press('s')
            self.last_gear_shift_time = current_time
            self.current_gear = new_gear
        elif new_gear < self.current_gear:
            # Shift down - press 'x'
            pydirectinput.press('x')
            self.last_gear_shift_time = current_time
            self.current_gear = new_gear
    
    def send_controls_to_gamepad(self, steering_value, accel, brake):
        """Send all control values to virtual Xbox controller"""
        try:
            # Steering
            self.gamepad.left_joystick_float(steering_value, 0.0)
            
            # Throttle (right trigger)
            throttle_value = 1.0 if accel else 0.0
            self.gamepad.right_trigger_float(throttle_value)
            
            # Brake (left trigger)
            brake_value = 1.0 if brake else 0.0
            self.gamepad.left_trigger_float(brake_value)
            
            self.gamepad.update()
        except Exception as e:
            print(f"Error sending to gamepad: {e}")
    
    def reset_to_safe_state(self):
        """Reset all controls to neutral/safe state"""
        try:
            self.gamepad.left_joystick_float(0.0, 0.0)  # Center steering
            self.gamepad.right_trigger_float(0.0)       # Release throttle
            self.gamepad.left_trigger_float(0.0)        # Release brake
            self.gamepad.update()
            self.smoothed_steering = 0.0
        except Exception as e:
            print(f"Error resetting to safe state: {e}")
    
    def display_status(self, x, y, z, steering, gear, accel, brake):
        """Display current status"""
        status_line = (f"[{self.packet_count:06d}] "
                      f"Z: {z:6.1f}° | "
                      f"Steering: {steering:+.3f} | "
                      f"Gear: {gear} | "
                      f"Accel: {int(accel)} | "
                      f"Brake: {int(brake)}")
        
        # Clear line and print status
        print(f"\r{status_line}", end="", flush=True)
    
    def display_debug_info(self, gear, accel, brake, steering):
        """Display debug information every 0.5 seconds"""
        current_time = time.time()
        if current_time - self.last_debug_time >= 0.5:
            print(f"\n[DEBUG] GEAR: {gear} | ACCEL: {int(accel)} | BRAKE: {int(brake)} | STEER: {steering:.2f}")
            self.last_debug_time = current_time
    
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
        print("  - Accelerator/Brake buttons for throttle/brake")
        print("  - Gear changes trigger 's' (up) / 'x' (down) keys")
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
                    
                    # Parse control data (JSON or legacy format)
                    message = data.decode('utf-8').strip()
                    x, y, z, gear, accel, brake = self.parse_control_data(message)
                    
                    if z is not None:
                        # Calculate steering from ESP32 z values (yaw, -90 to +90)
                        raw_steering = self.calculate_steering(z)
                        smoothed_steering = self.apply_smoothing(raw_steering)
                        
                        # Handle gear shifting
                        if gear is not None:
                            self.handle_gear_shift(gear)
                        
                        # Send all controls to gamepad
                        self.send_controls_to_gamepad(smoothed_steering, accel, brake)
                        
                        # Display status
                        self.display_status(x, y, z, smoothed_steering, gear, accel, brake)
                        
                        # Display debug info every 0.5s
                        self.display_debug_info(gear, accel, brake, smoothed_steering)
                
                except socket.timeout:
                    # Check for connection loss
                    current_time = time.time()
                    if current_time - self.last_data_time > 0.3:  # 300ms timeout
                        # No data for 300ms - enter safe state
                        self.reset_to_safe_state()
                        
                        if current_time - self.last_status_time > 1.0:
                            print(f"\n[WARN] No UDP data — entering safe state. Packets: {self.packet_count}")
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

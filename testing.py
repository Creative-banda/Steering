#!/usr/bin/env python3
"""
UDP Receiver for ESP32 Virtual Steering System
Receives orientation data (X, Y, Z) from ESP32 via UDP

Usage:
    python udp_receiver.py                      # Listen on all IPs, port 5555
    python udp_receiver.py 5556                 # Listen on all IPs, port 5556
    python udp_receiver.py 192.168.248.1        # Listen on specific IP, port 5555
    python udp_receiver.py 192.168.248.1 5556   # Listen on specific IP and port
"""

import socket
import sys
import time

# Configuration
UDP_IP = "0.0.0.0"  # Listen on all network interfaces (default)
UDP_PORT = 5555     # Default port (change if needed)

def get_local_ip_addresses():
    """Get all local IP addresses of this computer"""
    ip_addresses = []
    try:
        # Get hostname
        hostname = socket.gethostname()
        # Get all IP addresses for this host
        ip_list = socket.gethostbyname_ex(hostname)[2]
        # Filter out localhost
        ip_addresses = [ip for ip in ip_list if not ip.startswith("127.")]
    except Exception as e:
        print(f"Could not determine IP addresses: {e}")
    
    return ip_addresses

def check_network_compatibility(bind_ip, esp_ip=None):
    """Check if ESP32 IP is on the same subnet as the listening IP"""
    if not esp_ip or bind_ip == "0.0.0.0":
        return None
    
    # Simple subnet check (assumes /24 network)
    bind_subnet = '.'.join(bind_ip.split('.')[0:3])
    esp_subnet = '.'.join(esp_ip.split('.')[0:3])
    
    if bind_subnet != esp_subnet:
        return False
    return True

def main():
    print("=" * 70)
    print("  ESP32 Virtual Steering UDP Receiver")
    print("=" * 70)
    
    # Get local IP addresses
    local_ips = get_local_ip_addresses()
    
    # Parse command line arguments
    bind_ip = UDP_IP  # Default: listen on all interfaces
    port = UDP_PORT
    
    # Usage: python udp_receiver.py [IP] [port]
    # Examples:
    #   python udp_receiver.py                    -> 0.0.0.0:5555
    #   python udp_receiver.py 5556               -> 0.0.0.0:5556
    #   python udp_receiver.py 192.168.1.100      -> 192.168.1.100:5555
    #   python udp_receiver.py 192.168.1.100 5556 -> 192.168.1.100:5556
    
    if len(sys.argv) > 1:
        # Check if first arg is a port number or IP
        try:
            port = int(sys.argv[1])
            # It's a port number
        except ValueError:
            # It's an IP address
            bind_ip = sys.argv[1]
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    print(f"Invalid port number: {sys.argv[2]}")
                    print("Usage: python udp_receiver.py [IP_address] [port]")
                    sys.exit(1)
    
    # Display available IP addresses
    print("\n📍 Your Computer's IP Addresses:")
    if local_ips:
        for idx, ip in enumerate(local_ips, 1):
            print(f"   {idx}. {ip}")
    else:
        print("   Could not detect IP addresses")
    
    # Create UDP socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((bind_ip, port))
        sock.settimeout(1.0)  # 1 second timeout for periodic status updates
    except Exception as e:
        print(f"\n❌ Error creating socket: {e}")
        print(f"   Make sure port {port} is not already in use")
        if bind_ip != "0.0.0.0":
            print(f"   Make sure IP {bind_ip} exists on this computer")
        sys.exit(1)
    
    print(f"\n✓ Listening on {bind_ip}:{port}")
    
    # Show which IP to use for ESP32 configuration
    print("\n" + "=" * 70)
    print("📱 ESP32 CONFIGURATION INSTRUCTIONS:")
    print("=" * 70)
    if bind_ip == "0.0.0.0":
        print("  ✅ Listening on ALL network interfaces (RECOMMENDED)")
        print("  1. Connect to 'SteerSetup_XXXX' WiFi network on your phone/computer")
        print("  2. In the captive portal, enter ONE of these IP addresses:")
        if local_ips:
            for ip in local_ips:
                print(f"     → {ip}")
        else:
            print("     → (Use ipconfig to find your IP)")
        print(f"  3. Enter UDP port: {port}")
        print("  4. Save and wait for ESP32 to connect")
        print("\n  💡 TIP: Choose the IP on the SAME network as your ESP32!")
        print("     - If ESP32 connects to WiFi with 10.0.2.x, use 10.0.2.x IP")
        print("     - If ESP32 connects to WiFi with 192.168.x.x, use 192.168.x.x IP")
    else:
        print("  ⚠️  Listening on SPECIFIC IP - ESP32 must be on same subnet!")
        print("  1. Connect to 'SteerSetup_XXXX' WiFi network on your phone/computer")
        print(f"  2. In the captive portal, enter this IP: {bind_ip}")
        print(f"  3. Enter UDP port: {port}")
        print("  4. Save and wait for ESP32 to connect")
        print(f"\n  ⚠️  WARNING: ESP32 must get an IP like {'.'.join(bind_ip.split('.')[0:3])}.x")
        print("     If ESP32 gets different subnet (e.g., 10.0.2.x vs 192.168.x.x),")
        print("     it WON'T work! Use '0.0.0.0' to listen on all interfaces instead.")
    print("=" * 70)
    
    print("\n⏳ Waiting for data from ESP32...")
    print("-" * 70)
    
    packet_count = 0
    last_status_time = time.time()
    
    try:
        while True:
            try:
                # Receive data
                data, addr = sock.recvfrom(1024)
                packet_count += 1
                
                # Decode and parse
                message = data.decode('utf-8').strip()
                
                # Parse X:val|Y:val|Z:val format
                try:
                    parts = message.split('|')
                    x = int(parts[0].split(':')[1])
                    y = int(parts[1].split(':')[1])
                    z = int(parts[2].split(':')[1])
                    
                    # Display received data
                    print(f"[{packet_count:06d}] From {addr[0]}:{addr[1]} -> Roll: {x:4d}° | Pitch: {y:4d}° | Yaw: {z:4d}°")
                    
                    # Here you can add your steering control logic
                    # For example: control a virtual steering wheel, game, etc.
                    
                except (IndexError, ValueError) as e:
                    print(f"Error parsing data: {message} ({e})")
                    
            except socket.timeout:
                # Periodic status update when no data received
                current_time = time.time()
                if current_time - last_status_time > 5.0:
                    print(f"[Status] Packets received: {packet_count} | Waiting for data...")
                    last_status_time = current_time
                continue
                
    except KeyboardInterrupt:
        print("\n\nShutting down receiver...")
        print(f"Total packets received: {packet_count}")
        sock.close()
        sys.exit(0)

if __name__ == "__main__":
    main()

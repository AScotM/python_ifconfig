import os
import socket
import struct
import fcntl
import netifaces
import sys

# Color definitions
RESET_COLOR = "\033[0m"
GREY_COLOR = "\033[38;5;250m"  # Light Grey
SEP_COLOR = "\033[38;5;130m"   # Sepia

def format_bytes(size):
    """Format bytes into a human-readable format."""
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    unit_index = 0
    readable_size = float(size)

    while readable_size >= 1024.0 and unit_index < len(units) - 1:
        readable_size /= 1024.0
        unit_index += 1

    return f"{readable_size:.1f} {units[unit_index]}"

def get_mtu(interface):
    """Retrieve the MTU for a given network interface."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            mtu = fcntl.ioctl(s.fileno(), 0x8921, struct.pack('256s', interface.encode('utf-8')[:16]))[16:18]
            return struct.unpack('H', mtu)[0]
    except OSError as e:
        print(f"Error retrieving MTU for interface '{interface}': {e}")
        return None

def get_interface_info(interface):
    """Retrieve and print information for a given network interface."""
    print(SEP_COLOR + f"{interface}:" + RESET_COLOR)

    try:
        iface_flags = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [{}])[0]
        ip_address = iface_flags.get('addr', 'N/A')
        netmask = iface_flags.get('netmask', 'N/A')
        broadcast = iface_flags.get('broadcast', 'N/A')

        print(f"    inet: {ip_address}")
        print(f"    netmask: {netmask}")
        print(f"    broadcast: {broadcast}")

        mtu = get_mtu(interface)
        if mtu:
            print(f"    MTU: {mtu}")
        else:
            print("    MTU: Unable to retrieve")

    except Exception as e:
        print(f"    Error retrieving interface information: {e}")

def display_network_info():
    """Display network interface information."""
    print(GREY_COLOR + "Network Interfaces:" + RESET_COLOR)

    interfaces = netifaces.interfaces()

    for interface in interfaces:
        get_interface_info(interface)

def display_traffic_stats():
    """Display traffic statistics from /proc/net/dev."""
    if not os.path.exists("/proc/net/dev"):
        print("Unable to read /proc/net/dev. Make sure you are running this on a Linux system.")
        return

    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()

        print(GREY_COLOR + "\nTraffic Statistics:" + RESET_COLOR)

        for line in lines[2:]:
            if line.strip() == "":
                continue

            parts = line.split(":")
            if len(parts) < 2:
                continue

            iface = parts[0].strip()
            stats = parts[1].split()
            if len(stats) < 9:
                continue

            try:
                rx_bytes = int(stats[0])
                tx_bytes = int(stats[8])
            except ValueError:
                print(f"Skipping invalid stats for interface: {iface}")
                continue

            rx_formatted = format_bytes(rx_bytes)
            tx_formatted = format_bytes(tx_bytes)

            print(SEP_COLOR + f"  {iface}:" + RESET_COLOR)
            print("    RX: " + (GREY_COLOR + "No traffic" if rx_bytes == 0 else GREY_COLOR + rx_formatted) + RESET_COLOR)
            print("    TX: " + (GREY_COLOR + "No traffic" if tx_bytes == 0 else GREY_COLOR + tx_formatted) + RESET_COLOR)

    except Exception as e:
        print(f"Error reading traffic stats: {e}")

def main():
    if not sys.platform.startswith("linux"):
        print("This script is designed for Linux systems.")
        sys.exit(1)

    display_network_info()
    display_traffic_stats()

if __name__ == "__main__":
    main()


import os
import socket
import struct
import fcntl
import netifaces

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
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mtu = fcntl.ioctl(s.fileno(), 0x8921, struct.pack('256s', bytes(interface[:15], 'utf-8')))[16:18]
    return struct.unpack('H', mtu)[0]

def get_interface_info(interface):
    """Retrieve and print information for a given network interface."""
    print(SEP_COLOR + f"{interface}:" + RESET_COLOR)

    try:
        iface_flags = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]
        ip_address = iface_flags['addr']
        netmask = iface_flags['netmask']
        broadcast = iface_flags.get('broadcast', 'N/A')

        print(SEP_COLOR + f"    inet: {ip_address}" + RESET_COLOR)
        print(SEP_COLOR + f"    netmask: {netmask}" + RESET_COLOR)
        print(SEP_COLOR + f"    broadcast: {broadcast}" + RESET_COLOR)

        mtu = get_mtu(interface)
        print(SEP_COLOR + f"    MTU: {mtu}" + RESET_COLOR)

    except KeyError:
        print("    No IPv4 address found.")

def display_network_info():
    """Display network interface information."""
    print(GREY_COLOR + "Network Interfaces:" + RESET_COLOR)

    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        get_interface_info(interface)

def display_traffic_stats():
    """Display traffic statistics from /proc/net/dev."""
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()

        print(GREY_COLOR + "\nTraffic Statistics:" + RESET_COLOR)

        for line in lines[2:]:
            if line.strip() == "":
                continue

            parts = line.split(":")
            iface = parts[0].strip()
            stats = parts[1].split()

            rx_bytes = int(stats[0])
            tx_bytes = int(stats[8])

            rx_formatted = format_bytes(rx_bytes)
            tx_formatted = format_bytes(tx_bytes)

            print(SEP_COLOR + f"  {iface}:" + RESET_COLOR)
            if rx_bytes == 0:
                print("    RX: " + GREY_COLOR + "No traffic" + RESET_COLOR)
            else:
                print("    RX: " + GREY_COLOR + rx_formatted + RESET_COLOR)

            if tx_bytes == 0:
                print("    TX: " + GREY_COLOR + "No traffic" + RESET_COLOR)
            else:
                print("    TX: " + GREY_COLOR + tx_formatted + RESET_COLOR)

    except FileNotFoundError:
        print("Unable to read /proc/net/dev. Make sure you are running this on a Linux system.")

def main():
    display_network_info()
    display_traffic_stats()

if __name__ == "__main__":
    main()


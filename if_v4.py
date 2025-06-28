#!/usr/bin/env python3
"""Advanced Network Interface Monitor"""

import os
import socket
import struct
import fcntl
import netifaces
import sys
from types import SimpleNamespace

# Configuration
config = SimpleNamespace(
    FILTER_INTERFACES = {"eth0", "wlan0"},  # None to disable filtering
    COLOR_OUTPUT = True,
    BYTE_UNITS = ["B", "KiB", "MiB", "GiB", "TiB"],
    PROC_NET_DEV = "/proc/net/dev",
    SYSFS_NET_PATH = "/sys/class/net"
)

class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    GREY = "\033[38;5;250m"
    SEPIA = "\033[38;5;130m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    
    @classmethod
    def disable(cls):
        """Disable all coloring"""
        cls.RESET = cls.GREY = cls.SEPIA = cls.RED = cls.GREEN = ""

class InterfaceTraffic:
    """Track network interface statistics"""
    def __init__(self, name):
        self.name = name
        self.rx_bytes = 0
        self.tx_bytes = 0
        
    def update(self, rx, tx):
        self.rx_bytes = rx
        self.tx_bytes = tx
        
    @property
    def rx_human(self):
        return format_bytes(self.rx_bytes)
    
    @property 
    def tx_human(self):
        return format_bytes(self.tx_bytes)

def format_bytes(size):
    """Convert bytes to human-readable format"""
    unit_index = 0
    readable_size = float(size)
    
    while (readable_size >= 1024 and 
           unit_index < len(config.BYTE_UNITS) - 1):
        readable_size /= 1024
        unit_index += 1
        
    return f"{readable_size:.1f} {config.BYTE_UNITS[unit_index]}"

def get_mtu(interface):
    """Get MTU with multiple fallback methods"""
    try:
        # Method 1: ioctl
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            ifr = struct.pack('16sH', interface.encode(), 0)
            mtu = fcntl.ioctl(s.fileno(), 0x8921, ifr)[16:18]
            return struct.unpack('H', mtu)[0]
    except (OSError, struct.error):
        try:
            # Method 2: sysfs
            with open(f"{config.SYSFS_NET_PATH}/{interface}/mtu") as f:
                return int(f.read())
        except (IOError, ValueError):
            return None

def get_interface_info(interface):
    """Display detailed interface information"""
    print(f"{Colors.SEPIA}{interface}:{Colors.RESET}")
    
    try:
        addrs = netifaces.ifaddresses(interface)
        ipv4 = addrs.get(netifaces.AF_INET, [{}])[0]
        
        print(f"    inet: {ipv4.get('addr', 'N/A')}")
        print(f"    netmask: {ipv4.get('netmask', 'N/A')}")
        print(f"    broadcast: {ipv4.get('broadcast', 'N/A')}")
        
        if mtu := get_mtu(interface):
            print(f"    MTU: {mtu}")
    except Exception as e:
        print(f"{Colors.RED}    Error: {e}{Colors.RESET}")

def display_network_info():
    """Show all network interfaces"""
    print(f"{Colors.GREY}Network Interfaces:{Colors.RESET}")
    
    for interface in netifaces.interfaces():
        if (config.FILTER_INTERFACES and 
            interface not in config.FILTER_INTERFACES):
            continue
        get_interface_info(interface)

def display_traffic_stats():
    """Parse and display traffic statistics"""
    if not os.path.exists(config.PROC_NET_DEV):
        print(f"{Colors.RED}Error: {config.PROC_NET_DEV} not found{Colors.RESET}")
        return
        
    try:
        with open(config.PROC_NET_DEV) as f:
            lines = [l.strip() for l in f.readlines()[2:] if l.strip()]
            
        print(f"{Colors.GREY}\nTraffic Statistics:{Colors.RESET}")
        
        for line in lines:
            iface, stats = line.split(":")[0].strip(), line.split(":")[1].split()
            if config.FILTER_INTERFACES and iface not in config.FILTER_INTERFACES:
                continue
                
            try:
                traffic = InterfaceTraffic(iface)
                traffic.update(int(stats[0]), int(stats[8]))
                
                print(f"{Colors.SEPIA}  {iface}:{Colors.RESET}")
                print(f"    RX: {Colors.GREY}{traffic.rx_human}{Colors.RESET}")
                print(f"    TX: {Colors.GREY}{traffic.tx_human}{Colors.RESET}")
            except (IndexError, ValueError):
                continue
                
    except Exception as e:
        print(f"{Colors.RED}Error reading stats: {e}{Colors.RESET}")

def main():
    if not sys.platform.startswith("linux"):
        print(f"{Colors.RED}Error: Linux-only script{Colors.RESET}")
        sys.exit(1)
        
    if not config.COLOR_OUTPUT:
        Colors.disable()
        
    try:
        display_network_info()
        display_traffic_stats()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Interrupted{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{Colors.RED}Critical error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

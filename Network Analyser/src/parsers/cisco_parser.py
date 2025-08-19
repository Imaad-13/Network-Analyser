import re
import os
from typing import Dict, List, Optional, Tuple
from ..models.network_models import Device, Interface, DeviceType, Protocol

class CiscoConfigParser:
    def __init__(self):
        self.current_device = None
        self.current_interface = None
    
    def parse_config_file(self, file_path: str) -> Optional[Device]:
        """Parse a single Cisco config file"""
        if not os.path.exists(file_path):
            return None
        
        device_name = self._extract_device_name(file_path)
        device = Device(name=device_name, device_type=DeviceType.ROUTER)
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('interface '):
                interface, next_i = self._parse_interface_block(lines, i)
                if interface:
                    device.add_interface(interface)
                i = next_i
            elif line.startswith('router ospf'):
                device.routing_protocols.add(Protocol.OSPF)
                i += 1
            elif line.startswith('router bgp'):
                device.routing_protocols.add(Protocol.BGP)
                i += 1
            elif line.startswith('vlan '):
                vlan_id, vlan_name = self._parse_vlan(line)
                if vlan_id:
                    device.vlans[vlan_id] = vlan_name
                i += 1
            else:
                i += 1
        
        return device
    
    def _extract_device_name(self, file_path: str) -> str:
        """Extract device name from file path"""
        # Extract from path like "Conf/R1/config.dump"
        parts = file_path.split(os.sep)
        for part in reversed(parts):
            if part and part != 'config.dump':
                return part
        return "unknown_device"
    
    def _parse_interface_block(self, lines: List[str], start_idx: int) -> Tuple[Optional[Interface], int]:
        """Parse interface configuration block"""
        line = lines[start_idx].strip()
        
        # Extract interface name
        match = re.match(r'interface\s+(\S+)', line)
        if not match:
            return None, start_idx + 1
        
        interface_name = match.group(1)
        interface = Interface(name=interface_name)
        
        i = start_idx + 1
        while i < len(lines):
            line = lines[i].strip()
            
            # End of interface block
            if line and not line.startswith(' ') and not line.startswith('!'):
                break
            
            # Parse IP address
            ip_match = re.match(r'\s*ip address\s+(\S+)\s+(\S+)', line)
            if ip_match:
                interface.ip_address = ip_match.group(1)
                interface.subnet_mask = ip_match.group(2)
            
            # Parse VLAN
            vlan_match = re.match(r'\s*switchport access vlan\s+(\d+)', line)
            if vlan_match:
                interface.vlan_id = int(vlan_match.group(1))
            
            # Parse MTU
            mtu_match = re.match(r'\s*mtu\s+(\d+)', line)
            if mtu_match:
                interface.mtu = int(mtu_match.group(1))
            
            # Parse bandwidth
            bw_match = re.match(r'\s*bandwidth\s+(\d+)', line)
            if bw_match:
                interface.bandwidth = int(bw_match.group(1))
            
            # Check shutdown status
            if 'shutdown' in line and not line.strip().startswith('no shutdown'):
                interface.status = "down"
            
            i += 1
        
        return interface, i
    
    def _parse_vlan(self, line: str) -> Tuple[Optional[int], str]:
        """Parse VLAN definition"""
        match = re.match(r'vlan\s+(\d+)', line)
        if match:
            vlan_id = int(match.group(1))
            return vlan_id, f"VLAN_{vlan_id}"
        return None, ""
    
    def parse_directory(self, config_dir: str) -> Dict[str, Device]:
        """Parse all config files in a directory"""
        devices = {}
        
        for root, dirs, files in os.walk(config_dir):
            for file in files:
                if file.endswith('.dump') or file.endswith('.cfg'):
                    file_path = os.path.join(root, file)
                    device = self.parse_config_file(file_path)
                    if device:
                        devices[device.name] = device
        
        return devices

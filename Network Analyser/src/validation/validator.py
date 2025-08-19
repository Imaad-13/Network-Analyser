from typing import List, Dict, Set
from collections import defaultdict
import ipaddress
from ..models.network_models import NetworkTopology, Device, Protocol

class NetworkValidator:
    def __init__(self, topology: NetworkTopology):
        self.topology = topology
        self.issues = []
    
    def validate_all(self) -> List[str]:
        """Run all validation checks"""
        self.issues = []
        
        self._check_duplicate_ips()
        self._check_vlan_consistency()
        self._check_gateway_addresses()
        self._check_mtu_mismatches()
        self._check_network_loops()
        self._suggest_protocol_optimization()
        self._suggest_node_aggregation()
        
        return self.issues
    
    def _check_duplicate_ips(self):
        """Check for duplicate IP addresses within same VLAN/subnet"""
        ip_to_devices = defaultdict(list)
        
        for device_name, device in self.topology.devices.items():
            for interface in device.interfaces.values():
                if interface.ip_address:
                    key = f"{interface.ip_address}_{interface.vlan_id or 'no_vlan'}"
                    ip_to_devices[key].append(f"{device_name}:{interface.name}")
        
        for ip_vlan, device_list in ip_to_devices.items():
            if len(device_list) > 1:
                ip = ip_vlan.split('_')[0]
                self.issues.append(f"Duplicate IP {ip} found on: {', '.join(device_list)}")
    
    def _check_vlan_consistency(self):
        """Check VLAN label consistency"""
        vlan_names = defaultdict(set)
        
        for device in self.topology.devices.values():
            for vlan_id, vlan_name in device.vlans.items():
                vlan_names[vlan_id].add(vlan_name)
        
        for vlan_id, names in vlan_names.items():
            if len(names) > 1:
                self.issues.append(f"VLAN {vlan_id} has inconsistent names: {', '.join(names)}")
    
    def _check_gateway_addresses(self):
        """Check for incorrect gateway addresses"""
        for device_name, device in self.topology.devices.items():
            for interface in device.interfaces.values():
                if interface.ip_address and interface.subnet_mask:
                    try:
                        network = ipaddress.IPv4Network(
                            f"{interface.ip_address}/{interface.subnet_mask}", 
                            strict=False
                        )
                        
                        # Check if IP is network or broadcast address
                        ip_addr = ipaddress.IPv4Address(interface.ip_address)
                        if ip_addr == network.network_address:
                            self.issues.append(f"Device {device_name}:{interface.name} using network address as IP")
                        elif ip_addr == network.broadcast_address:
                            self.issues.append(f"Device {device_name}:{interface.name} using broadcast address as IP")
                            
                    except Exception:
                        self.issues.append(f"Invalid IP/subnet on {device_name}:{interface.name}")
    
    def _check_mtu_mismatches(self):
        """Check for MTU mismatches on connected interfaces"""
        for link in self.topology.links:
            device1 = self.topology.devices[link.device1]
            device2 = self.topology.devices[link.device2]
            
            interface1 = device1.interfaces.get(link.interface1)
            interface2 = device2.interfaces.get(link.interface2)
            
            if interface1 and interface2:
                if interface1.mtu != interface2.mtu:
                    self.issues.append(
                        f"MTU mismatch between {link.device1}:{link.interface1} ({interface1.mtu}) "
                        f"and {link.device2}:{link.interface2} ({interface2.mtu})"
                    )
    
    def _check_network_loops(self):
        """Simple loop detection using DFS"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(device, path):
            visited.add(device)
            rec_stack.add(device)
            
            for neighbor in self.topology.get_neighbors(device):
                if neighbor not in visited:
                    if has_cycle(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    cycle_path = path[path.index(neighbor):] + [neighbor]
                    self.issues.append(f"Potential loop detected: {' -> '.join(cycle_path)}")
                    return True
            
            rec_stack.remove(device)
            return False
        
        for device_name in self.topology.devices:
            if device_name not in visited:
                has_cycle(device_name, [device_name])
    
    def _suggest_protocol_optimization(self):
        """Suggest BGP vs OSPF based on network size"""
        total_devices = len(self.topology.devices)
        total_links = len(self.topology.links)
        
        # Simple heuristic: BGP for larger networks
        if total_devices > 20 or total_links > 30:
            ospf_devices = [name for name, device in self.topology.devices.items() 
                          if Protocol.OSPF in device.routing_protocols]
            if ospf_devices:
                self.issues.append(
                    f"Consider using BGP instead of OSPF for large network. "
                    f"OSPF devices: {', '.join(ospf_devices[:5])}{'...' if len(ospf_devices) > 5 else ''}"
                )
    
    def _suggest_node_aggregation(self):
        """Suggest opportunities for node aggregation"""
        # Find devices with only 2 connections (potential aggregation candidates)
        for device_name, device in self.topology.devices.items():
            neighbors = self.topology.get_neighbors(device_name)
            if len(neighbors) == 2:
                active_interfaces = [iface for iface in device.interfaces.values() 
                                   if iface.status == "up" and iface.ip_address]
                if len(active_interfaces) <= 2:
                    self.issues.append(
                        f"Device {device_name} might be aggregated with neighbors: {', '.join(neighbors)}"
                    )

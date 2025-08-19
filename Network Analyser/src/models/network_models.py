from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum
import json

class DeviceType(Enum):
    ROUTER = "router"
    SWITCH = "switch"
    HOST = "host"

class Protocol(Enum):
    OSPF = "ospf"
    BGP = "bgp"
    STATIC = "static"

@dataclass
class Interface:
    name: str
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    vlan_id: Optional[int] = None
    mtu: int = 1500
    bandwidth: Optional[int] = None  # in Mbps
    status: str = "up"
    
    def get_network(self) -> Optional[str]:
        """Calculate network address from IP and mask"""
        if self.ip_address and self.subnet_mask:
            # Simple implementation - you can enhance with ipaddress module
            return f"{self.ip_address}/{self.subnet_mask}"
        return None

@dataclass
class Device:
    name: str
    device_type: DeviceType
    interfaces: Dict[str, Interface] = field(default_factory=dict)
    routing_protocols: Set[Protocol] = field(default_factory=set)
    vlans: Dict[int, str] = field(default_factory=dict)  # vlan_id -> vlan_name
    
    def add_interface(self, interface: Interface):
        self.interfaces[interface.name] = interface
    
    def get_management_ip(self) -> Optional[str]:
        """Get the first available IP for management"""
        for interface in self.interfaces.values():
            if interface.ip_address:
                return interface.ip_address
        return None

@dataclass
class Link:
    device1: str
    interface1: str
    device2: str
    interface2: str
    bandwidth: Optional[int] = None
    cost: int = 1
    
    def __hash__(self):
        # Make links bidirectional by sorting device names
        devices = sorted([
            (self.device1, self.interface1),
            (self.device2, self.interface2)
        ])
        return hash(tuple(devices))

@dataclass
class NetworkTopology:
    devices: Dict[str, Device] = field(default_factory=dict)
    links: Set[Link] = field(default_factory=set)
    subnets: Dict[str, List[str]] = field(default_factory=dict)  # subnet -> [device_names]
    
    def add_device(self, device: Device):
        self.devices[device.name] = device
    
    def add_link(self, link: Link):
        self.links.add(link)
    
    def get_neighbors(self, device_name: str) -> List[str]:
        """Get all neighboring devices"""
        neighbors = []
        for link in self.links:
            if link.device1 == device_name:
                neighbors.append(link.device2)
            elif link.device2 == device_name:
                neighbors.append(link.device1)
        return neighbors
    
    def to_dict(self) -> dict:
        """Serialize topology for JSON export"""
        return {
            'devices': {name: {
                'type': device.device_type.value,
                'interfaces': {iface_name: {
                    'ip': iface.ip_address,
                    'subnet_mask': iface.subnet_mask,
                    'vlan': iface.vlan_id,
                    'mtu': iface.mtu,
                    'bandwidth': iface.bandwidth
                } for iface_name, iface in device.interfaces.items()},
                'protocols': [p.value for p in device.routing_protocols],
                'vlans': device.vlans
            } for name, device in self.devices.items()},
            'links': [{
                'device1': link.device1,
                'interface1': link.interface1,
                'device2': link.device2,
                'interface2': link.interface2,
                'bandwidth': link.bandwidth
            } for link in self.links]
        }

import ipaddress
from typing import Dict, List, Set
from ..models.network_models import Device, Link, NetworkTopology, Interface

class TopologyBuilder:
    def __init__(self):
        self.topology = NetworkTopology()
    
    def build_topology(self, devices: Dict[str, Device]) -> NetworkTopology:
        """Build network topology from parsed devices"""
        # Add all devices
        for device in devices.values():
            self.topology.add_device(device)
        
        # Discover links based on IP subnets
        self._discover_links(devices)
        
        # Build subnet mappings
        self._build_subnet_mappings(devices)
        
        return self.topology
    
    def _discover_links(self, devices: Dict[str, Device]):
        """Discover links between devices based on shared subnets"""
        subnet_to_devices = {}
        
        # Group interfaces by subnet
        for device_name, device in devices.items():
            for interface in device.interfaces.values():
                if interface.ip_address and interface.subnet_mask:
                    try:
                        network = ipaddress.IPv4Network(
                            f"{interface.ip_address}/{interface.subnet_mask}", 
                            strict=False
                        )
                        subnet_str = str(network.network_address) + "/" + str(network.prefixlen)
                        
                        if subnet_str not in subnet_to_devices:
                            subnet_to_devices[subnet_str] = []
                        
                        subnet_to_devices[subnet_str].append((device_name, interface))
                    except Exception as e:
                        print(f"Error parsing IP {interface.ip_address}/{interface.subnet_mask}: {e}")
        
        # Create links for devices in same subnet
        for subnet, device_interfaces in subnet_to_devices.items():
            if len(device_interfaces) >= 2:
                # Create links between all pairs in the subnet
                for i in range(len(device_interfaces)):
                    for j in range(i + 1, len(device_interfaces)):
                        device1_name, interface1 = device_interfaces[i]
                        device2_name, interface2 = device_interfaces[j]
                        
                        link = Link(
                            device1=device1_name,
                            interface1=interface1.name,
                            device2=device2_name,
                            interface2=interface2.name,
                            bandwidth=min(
                                interface1.bandwidth or 100,
                                interface2.bandwidth or 100
                            )
                        )
                        self.topology.add_link(link)
    
    def _build_subnet_mappings(self, devices: Dict[str, Device]):
        """Build subnet to devices mapping"""
        for device_name, device in devices.items():
            for interface in device.interfaces.values():
                network = interface.get_network()
                if network:
                    if network not in self.topology.subnets:
                        self.topology.subnets[network] = []
                    if device_name not in self.topology.subnets[network]:
                        self.topology.subnets[network].append(device_name)
    
    def detect_missing_components(self) -> List[str]:
        """Detect missing network components"""
        issues = []
        
        # Check for isolated devices
        for device_name in self.topology.devices:
            neighbors = self.topology.get_neighbors(device_name)
            if not neighbors:
                issues.append(f"Device {device_name} appears to be isolated (no connections found)")
        
        # Check for subnets with only one device
        for subnet, device_list in self.topology.subnets.items():
            if len(device_list) == 1:
                issues.append(f"Subnet {subnet} has only one device ({device_list[0]}) - possible missing switch/endpoint")
        
        return issues

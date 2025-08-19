#!/usr/bin/env python3
import json
import argparse
from src.parsers.cisco_parser import CiscoConfigParser
from src.topology.topology_builder import TopologyBuilder
from src.validation.validator import NetworkValidator

def main():
    parser = argparse.ArgumentParser(description='Network Topology Analyzer - MVP')
    parser.add_argument('config_dir', help='Directory containing router config files')
    parser.add_argument('--output', '-o', help='Output JSON file for topology', default='topology.json')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🔹 Network Topology Analyzer - MVP Phase")
    print("=" * 50)
    
    # Phase 1: Parse configurations
    print("1️⃣ Parsing configuration files...")
    parser_engine = CiscoConfigParser()
    devices = parser_engine.parse_directory(args.config_dir)
    print(f"   ✅ Parsed {len(devices)} devices: {', '.join(devices.keys())}")
    
    # Phase 2: Build topology
    print("\n2️⃣ Building network topology...")
    builder = TopologyBuilder()
    topology = builder.build_topology(devices)
    print(f"   ✅ Created topology with {len(topology.links)} links")
    
    # Check for missing components
    missing = builder.detect_missing_components()
    if missing:
        print("   ⚠️  Missing components detected:")
        for issue in missing:
            print(f"      - {issue}")
    
    # Phase 3: Validate configuration
    print("\n3️⃣ Validating network configuration...")
    validator = NetworkValidator(topology)
    issues = validator.validate_all()
    
    if issues:
        print(f"   ⚠️  Found {len(issues)} configuration issues:")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ No configuration issues found")
    
    # Export topology
    print(f"\n4️⃣ Exporting topology to {args.output}...")
    with open(args.output, 'w') as f:
        json.dump(topology.to_dict(), f, indent=2)
    print("   ✅ Export complete")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   • Devices: {len(topology.devices)}")
    print(f"   • Links: {len(topology.links)}")
    print(f"   • Subnets: {len(topology.subnets)}")
    print(f"   • Issues: {len(issues)}")
    print(f"   • Missing components: {len(missing)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Read package configuration from packages.yaml or packages.txt
and output in JSON format for GitHub Actions workflow.
"""

import json
import os
import sys
from pathlib import Path


def read_yaml_config(config_file):
    """Read packages from YAML configuration file."""
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    packages_data = []
    
    for pkg in config.get('packages', []):
        if not isinstance(pkg, dict):
            print(f"Warning: Invalid package entry: {pkg}", file=sys.stderr)
            continue
        
        name = pkg.get('name')
        if not name:
            print(f"Warning: Package entry missing name: {pkg}", file=sys.stderr)
            continue
        
        # Build package spec
        spec = name
        if 'version' in pkg:
            spec = f"{name}{pkg['version']}"
        
        package_info = {
            'spec': spec,
            'name': name,
            'source': pkg.get('source', 'pypi'),
            'host_dependencies': pkg.get('host_dependencies', []),
            'pip_dependencies': pkg.get('pip_dependencies', []),
            'patches': pkg.get('patches', []),
        }
        
        # Add URL if specified
        if 'url' in pkg:
            package_info['url'] = pkg['url']
        
        packages_data.append(package_info)
    
    return packages_data


def read_txt_config(config_file):
    """Read packages from simple text file (backward compatibility)."""
    packages_data = []
    
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Simple format: just package spec
            # Extract package name from spec
            name = line.split('==')[0].split('>=')[0].split('<=')[0].split('!=')[0].split('~=')[0].split('[')[0]
            
            package_info = {
                'spec': line,
                'name': name,
                'source': 'pypi',
                'host_dependencies': [],
                'pip_dependencies': [],
                'patches': [],
            }
            
            packages_data.append(package_info)
    
    return packages_data


def main():
    # Check for YAML config first, fall back to txt
    yaml_file = Path('packages.yaml')
    txt_file = Path('packages.txt')
    
    if yaml_file.exists():
        print("Reading from packages.yaml", file=sys.stderr)
        packages_data = read_yaml_config(yaml_file)
    elif txt_file.exists():
        print("Reading from packages.txt (backward compatibility mode)", file=sys.stderr)
        packages_data = read_txt_config(txt_file)
    else:
        print("Error: Neither packages.yaml nor packages.txt found", file=sys.stderr)
        sys.exit(1)
    
    # Output as JSON
    print(json.dumps(packages_data))
    
    # Also output summary to stderr for logging
    print(f"\nFound {len(packages_data)} packages:", file=sys.stderr)
    for pkg in packages_data:
        info_parts = []
        if pkg['host_dependencies']:
            info_parts.append(f"host deps: {', '.join(pkg['host_dependencies'])}")
        if pkg['patches']:
            info_parts.append(f"patches: {len(pkg['patches'])}")
        info = f" ({'; '.join(info_parts)})" if info_parts else ""
        print(f"  - {pkg['spec']}{info}", file=sys.stderr)


if __name__ == '__main__':
    main()

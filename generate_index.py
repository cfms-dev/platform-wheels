#!/usr/bin/env python3
"""
Generate a PyPI-like index for wheels to be hosted on GitHub Pages.

This script creates:
1. A root index.html listing all available packages
2. Per-package index.html files listing all wheels for that package
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import hashlib
import re


def get_package_name_from_wheel(wheel_filename):
    """
    Extract the package name from a wheel filename, preserving case.
    Wheel format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
    
    Note: Package names preserve their original capitalization to allow
    packages with the same name but different cases (e.g., 'PyYAML' vs 'pyyaml')
    to be kept separate in the index.
    """
    # Remove .whl extension
    name_without_ext = wheel_filename.replace('.whl', '')
    
    # Split on hyphens
    parts = name_without_ext.split('-')
    
    # Find the first part that looks like a version (starts with a digit)
    # According to PEP 427, version is the second component and starts with a digit
    for i, part in enumerate(parts):
        if part and part[0].isdigit():
            # Everything before this is the package name
            package_name = '-'.join(parts[:i])
            # Normalize underscores to hyphens but preserve case
            return package_name.replace('_', '-')
    
    # Fallback: if no version found, assume first part is package name
    if parts:
        return parts[0].replace('_', '-')
    return None


def calculate_hash(filepath, algorithm='sha256'):
    """Calculate hash of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def generate_package_index(package_name, wheels, output_dir):
    """Generate index.html for a specific package."""
    package_dir = output_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Links for {package_name}</title>
</head>
<body>
    <h1>Links for {package_name}</h1>
"""
    
    for wheel_file, wheel_path in wheels:
        # Calculate hash
        file_hash = calculate_hash(wheel_path)
        
        # Copy wheel to package directory
        dest_path = package_dir / wheel_file
        if wheel_path != dest_path:
            import shutil
            shutil.copy2(wheel_path, dest_path)
        
        # Add link with hash
        html_content += f'    <a href="{wheel_file}#sha256={file_hash}">{wheel_file}</a><br/>\n'
    
    html_content += """</body>
</html>
"""
    
    index_path = package_dir / 'index.html'
    index_path.write_text(html_content)
    print(f"Generated index for {package_name} at {index_path}")


def generate_root_index(packages, output_dir):
    """Generate the root index.html listing all packages."""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Platform Wheels Index</title>
</head>
<body>
    <h1>Platform Wheels Index</h1>
    <p>Simple PyPI-like index for platform-specific Python wheels.</p>
"""
    
    for package_name in sorted(packages):
        html_content += f'    <a href="{package_name}/">{package_name}</a><br/>\n'
    
    html_content += """</body>
</html>
"""
    
    index_path = output_dir / 'index.html'
    index_path.write_text(html_content)
    print(f"Generated root index at {index_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_index.py <wheels_dir> <output_dir>")
        print("  wheels_dir: Directory containing .whl files")
        print("  output_dir: Directory where index will be generated")
        sys.exit(1)
    
    wheels_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    if not wheels_dir.exists():
        print(f"Error: Wheels directory {wheels_dir} does not exist")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all wheel files and group by package
    packages = defaultdict(list)
    
    for wheel_path in wheels_dir.glob('**/*.whl'):
        wheel_file = wheel_path.name
        package_name = get_package_name_from_wheel(wheel_file)
        
        if package_name:
            packages[package_name].append((wheel_file, wheel_path))
            print(f"Found wheel: {wheel_file} for package: {package_name}")
        else:
            print(f"Warning: Could not determine package name for {wheel_file}")
    
    if not packages:
        print("Warning: No wheel files found")
        # Create empty index anyway
        generate_root_index([], output_dir)
        return
    
    # Generate per-package indexes
    for package_name, wheels in packages.items():
        generate_package_index(package_name, wheels, output_dir)
    
    # Generate root index
    generate_root_index(packages.keys(), output_dir)
    
    print(f"\nIndex generation complete!")
    print(f"Total packages: {len(packages)}")
    print(f"Total wheels: {sum(len(wheels) for wheels in packages.values())}")


if __name__ == '__main__':
    main()

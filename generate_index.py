#!/usr/bin/env python3
"""
Generate a PyPI-like index for wheels to be hosted on GitHub Pages.

This script creates:
1. A root index.html listing all available packages
2. Per-package index.html files listing all wheels for that package
3. Alias indexes for packages with aliases specified
"""

import os
import sys
import json
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


def rename_wheel_for_alias(wheel_filename, old_name, new_name):
    """
    Rename a wheel file to use a different package name (for aliases).
    
    Args:
        wheel_filename: Original wheel filename
        old_name: Original package name (case-insensitive comparison)
        new_name: New package name to use in the filename
    
    Returns:
        New wheel filename with the package name replaced
    """
    # Remove .whl extension
    name_without_ext = wheel_filename.replace('.whl', '')
    
    # Split on hyphens
    parts = name_without_ext.split('-')
    
    # Find the first part that looks like a version (starts with a digit)
    for i, part in enumerate(parts):
        if part and part[0].isdigit():
            # Replace the package name parts (everything before version)
            old_package_parts = parts[:i]
            old_package_name = '-'.join(old_package_parts).replace('_', '-')
            
            # Check if this matches the old_name (case-insensitive)
            if old_package_name.lower() == old_name.lower():
                # Replace with new name (preserve underscores if original had them)
                new_package_name = new_name.replace('-', '_') if '_' in '-'.join(old_package_parts) else new_name
                new_parts = [new_package_name] + parts[i:]
                return '-'.join(new_parts) + '.whl'
    
    # If we can't parse it properly, return original
    return wheel_filename


def calculate_hash(filepath, algorithm='sha256'):
    """Calculate hash of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def generate_package_index(package_name, wheels, output_dir, rename_from=None, rename_to=None):
    """
    Generate index.html for a specific package.
    
    Args:
        package_name: Name for the package directory
        wheels: List of (wheel_file, wheel_path) tuples
        output_dir: Output directory for the index
        rename_from: Original package name (for renaming wheels in alias indexes)
        rename_to: New package name to use in wheel filenames (for alias indexes)
    """
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
        
        # Rename wheel file if this is an alias index
        if rename_from and rename_to:
            display_wheel_file = rename_wheel_for_alias(wheel_file, rename_from, rename_to)
        else:
            display_wheel_file = wheel_file
        
        # Copy wheel to package directory
        dest_path = package_dir / display_wheel_file
        if wheel_path != dest_path:
            import shutil
            shutil.copy2(wheel_path, dest_path)
        
        # Add link with hash
        html_content += f'    <a href="{display_wheel_file}#sha256={file_hash}">{display_wheel_file}</a><br/>\n'
    
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
        print("Usage: generate_index.py <wheels_dir> <output_dir> [packages_metadata.json]")
        print("  wheels_dir: Directory containing .whl files")
        print("  output_dir: Directory where index will be generated")
        print("  packages_metadata.json: Optional JSON file with package metadata (including aliases)")
        sys.exit(1)
    
    wheels_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    packages_metadata_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not wheels_dir.exists():
        print(f"Error: Wheels directory {wheels_dir} does not exist")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load package metadata if provided
    package_aliases = {}  # Maps package name (from wheel) to configured name
    alias_to_canonical = {}  # Maps alias back to the canonical wheel package name
    if packages_metadata_file and packages_metadata_file.exists():
        print(f"Loading package metadata from {packages_metadata_file}")
        with open(packages_metadata_file, 'r') as f:
            packages_metadata = json.load(f)
            for pkg in packages_metadata:
                if 'alias' in pkg and pkg['alias']:
                    # Create bidirectional mapping
                    # The 'name' field is the configured name (e.g., 'pyyaml')
                    # The 'alias' field is what the wheel is actually named (e.g., 'PyYAML')
                    configured_name = pkg['name']
                    alias_name = pkg['alias']
                    
                    # Map from alias (wheel name) to configured name
                    package_aliases[alias_name.lower()] = configured_name
                    # Map from configured name back to alias (wheel name) 
                    alias_to_canonical[configured_name.lower()] = alias_name
                    
                    print(f"Package mapping: config name '{configured_name}' <-> wheel name '{alias_name}'")
    
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
    
    # Track all package names (including aliases) for the root index
    all_package_names = set()
    
    # Generate per-package indexes
    for package_name, wheels in packages.items():
        # Generate index for the wheel's actual package name
        generate_package_index(package_name, wheels, output_dir)
        all_package_names.add(package_name)
        
        # Check if this wheel package name has a configured alias
        # Look for mapping using case-insensitive match
        configured_name = package_aliases.get(package_name.lower())
        
        if configured_name and configured_name != package_name:
            print(f"Generating additional index: {configured_name} -> {package_name}")
            # Generate index under the configured name with renamed wheels
            generate_package_index(configured_name, wheels, output_dir, 
                                 rename_from=package_name, rename_to=configured_name)
            all_package_names.add(configured_name)
    
    # Generate root index with all package names (including aliases)
    generate_root_index(all_package_names, output_dir)
    
    print(f"\nIndex generation complete!")
    print(f"Total packages: {len(packages)}")
    print(f"Total package indexes (including aliases): {len(all_package_names)}")
    print(f"Total wheels: {sum(len(wheels) for wheels in packages.values())}")


if __name__ == '__main__':
    main()

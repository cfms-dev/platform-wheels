#!/usr/bin/env python3
"""
Read package configuration from recipes/, packages.yaml, or packages.txt
and output in JSON format for GitHub Actions workflow.

Configuration Priority:
1. recipes/ directory (each package in recipes/package-name/recipe.yaml)
2. packages.yaml (centralized configuration)
3. packages.txt (simple list for backward compatibility)
"""

import json
import os
import sys
from pathlib import Path


def read_recipe(recipe_dir):
    """Read a single recipe from recipes/package-name/recipe.yaml."""
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    recipe_file = recipe_dir / 'recipe.yaml'
    if not recipe_file.exists():
        return None
    
    with open(recipe_file, 'r') as f:
        recipe = yaml.safe_load(f)
    
    if not recipe or 'package' not in recipe:
        print(f"Warning: Invalid recipe in {recipe_dir}", file=sys.stderr)
        return None
    
    pkg = recipe['package']
    name = pkg.get('name')
    if not name:
        print(f"Warning: Recipe missing package name in {recipe_dir}", file=sys.stderr)
        return None
    
    # Build package spec
    spec = name
    if 'version' in pkg and pkg['version']:
        spec = f"{name}{pkg['version']}"
    
    package_info = {
        'spec': spec,
        'name': name,
        'alias': pkg.get('alias', ''),
        'source': recipe.get('source', pkg.get('source', 'pypi')),
        'host_dependencies': recipe.get('host_dependencies', []),
        'pip_dependencies': recipe.get('pip_dependencies', []),
        'build_dependencies': recipe.get('build_dependencies', []),
        'patches': [],
        'cibw_environment': '',  # Will be formatted as CIBW_ENVIRONMENT string
        'cibw_before_all': recipe.get('cibw_before_all', ''),
        'cibw_config_settings': recipe.get('cibw_config_settings', ''),
        'skip_platforms': recipe.get('skip_platforms', []),
    }
    
    # Convert cibw_environment dict to CIBW_ENVIRONMENT string format
    if 'cibw_environment' in recipe and recipe['cibw_environment']:
        env_dict = recipe['cibw_environment']
        if isinstance(env_dict, dict):
            # Format as VAR1=val1 VAR2=val2
            env_pairs = [f'{k}={v}' for k, v in env_dict.items()]
            package_info['cibw_environment'] = ' '.join(env_pairs)
    
    # Add URL if specified
    if 'url' in recipe:
        package_info['url'] = recipe['url']
    elif 'url' in pkg:
        package_info['url'] = pkg['url']
    
    # Handle patches - convert relative paths to be relative to repository root
    patches = recipe.get('patches', [])
    # Handle case where patches key exists but is None (e.g., all patches commented out)
    if patches is None:
        patches = []
    for patch in patches:
        if patch.startswith('http://') or patch.startswith('https://'):
            # External URL patch
            package_info['patches'].append(patch)
        else:
            # Local patch file relative to recipe directory
            patch_path = recipe_dir / patch
            if patch_path.exists():
                # Convert to path relative to repository root for $GITHUB_WORKSPACE
                # This ensures it works on both Linux and macOS runners
                relative_to_repo = os.path.relpath(patch_path, Path.cwd())
                package_info['patches'].append(relative_to_repo)
            else:
                print(f"Warning: Patch file not found: {patch_path}", file=sys.stderr)
    
    return package_info


def read_recipes_dir():
    """Read all recipes from recipes/ directory."""
    recipes_dir = Path('recipes')
    if not recipes_dir.exists():
        return []
    
    packages_data = []
    
    # Iterate through each subdirectory in recipes/
    for recipe_dir in sorted(recipes_dir.iterdir()):
        if recipe_dir.is_dir():
            package_info = read_recipe(recipe_dir)
            if package_info:
                packages_data.append(package_info)
    
    return packages_data


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
            'alias': pkg.get('alias', ''),
            'source': pkg.get('source', 'pypi'),
            'host_dependencies': pkg.get('host_dependencies', []),
            'pip_dependencies': pkg.get('pip_dependencies', []),
            'build_dependencies': pkg.get('build_dependencies', []),
            'patches': pkg.get('patches', []),
            'cibw_environment': '',
            'cibw_before_all': pkg.get('cibw_before_all', ''),
            'cibw_config_settings': pkg.get('cibw_config_settings', ''),
        }
        
        # Convert cibw_environment dict to CIBW_ENVIRONMENT string format
        if 'cibw_environment' in pkg and pkg['cibw_environment']:
            env_dict = pkg['cibw_environment']
            if isinstance(env_dict, dict):
                # Format as VAR1=val1 VAR2=val2
                env_pairs = [f'{k}={v}' for k, v in env_dict.items()]
                package_info['cibw_environment'] = ' '.join(env_pairs)
        
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
                'alias': '',
                'source': 'pypi',
                'host_dependencies': [],
                'pip_dependencies': [],
                'build_dependencies': [],
                'patches': [],
                'cibw_environment': '',
                'cibw_before_all': '',
                'cibw_config_settings': '',
            }
            
            packages_data.append(package_info)
    
    return packages_data


def topological_sort(packages_data):
    """Sort packages based on build_dependencies using topological sort."""
    # Build a mapping from package names to package data
    pkg_map = {pkg['name']: pkg for pkg in packages_data}
    
    # Build adjacency list (package -> list of packages that depend on it)
    graph = {pkg['name']: [] for pkg in packages_data}
    in_degree = {pkg['name']: 0 for pkg in packages_data}
    
    for pkg in packages_data:
        for dep in pkg.get('build_dependencies', []):
            if dep in pkg_map:
                graph[dep].append(pkg['name'])
                in_degree[pkg['name']] += 1
            else:
                print(f"Warning: Package {pkg['name']} depends on {dep} which is not in the package list", file=sys.stderr)
    
    # Kahn's algorithm for topological sort
    queue = [name for name, degree in in_degree.items() if degree == 0]
    sorted_packages = []
    
    while queue:
        # Sort queue for deterministic output
        queue.sort()
        current = queue.pop(0)
        sorted_packages.append(pkg_map[current])
        
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Check for cycles
    if len(sorted_packages) != len(packages_data):
        remaining = [name for name, degree in in_degree.items() if degree > 0]
        print(f"Error: Circular dependency detected among packages: {', '.join(remaining)}", file=sys.stderr)
        sys.exit(1)
    
    return sorted_packages


def main():
    # Priority: recipes/ > packages.yaml > packages.txt
    recipes_dir = Path('recipes')
    yaml_file = Path('packages.yaml')
    txt_file = Path('packages.txt')
    
    packages_data = []
    
    # 1. Check for recipes directory
    if recipes_dir.exists() and any(recipes_dir.iterdir()):
        print("Reading from recipes/ directory", file=sys.stderr)
        packages_data = read_recipes_dir()
    
    # 2. Check for packages.yaml
    if yaml_file.exists():
        print("Reading from packages.yaml", file=sys.stderr)
        yaml_packages = read_yaml_config(yaml_file)
        
        # Merge with recipes, avoiding duplicates
        existing_names = {pkg['name'] for pkg in packages_data}
        for pkg in yaml_packages:
            if pkg['name'] not in existing_names:
                packages_data.append(pkg)
            else:
                print(f"  Note: {pkg['name']} already defined in recipes/, skipping from packages.yaml", file=sys.stderr)
    
    # 3. Fall back to packages.txt
    if not packages_data and txt_file.exists():
        print("Reading from packages.txt (backward compatibility mode)", file=sys.stderr)
        packages_data = read_txt_config(txt_file)
    
    if not packages_data:
        print("Error: No package configuration found (checked recipes/, packages.yaml, packages.txt)", file=sys.stderr)
        sys.exit(1)
    
    # Sort packages by build dependencies
    packages_data = topological_sort(packages_data)
    
    # Output as JSON
    print(json.dumps(packages_data))
    
    # Also output summary to stderr for logging
    print(f"\nFound {len(packages_data)} packages:", file=sys.stderr)
    for pkg in packages_data:
        info_parts = []
        if pkg['host_dependencies']:
            info_parts.append(f"host deps: {', '.join(pkg['host_dependencies'])}")
        if pkg.get('build_dependencies'):
            info_parts.append(f"build deps: {', '.join(pkg['build_dependencies'])}")
        if pkg['patches']:
            info_parts.append(f"patches: {len(pkg['patches'])}")
        info = f" ({'; '.join(info_parts)})" if info_parts else ""
        print(f"  - {pkg['spec']}{info}", file=sys.stderr)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test dependency resolution and build order functionality.
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from read_packages import topological_sort


def test_basic_dependency_order():
    """Test that packages are sorted correctly based on dependencies."""
    packages = [
        {'name': 'package-c', 'build_dependencies': ['package-a', 'package-b']},
        {'name': 'package-b', 'build_dependencies': ['package-a']},
        {'name': 'package-a', 'build_dependencies': []},
    ]
    
    sorted_packages = topological_sort(packages)
    names = [pkg['name'] for pkg in sorted_packages]
    
    # package-a should come before package-b and package-c
    # package-b should come before package-c
    assert names.index('package-a') < names.index('package-b'), \
        f"package-a should come before package-b, got order: {names}"
    assert names.index('package-a') < names.index('package-c'), \
        f"package-a should come before package-c, got order: {names}"
    assert names.index('package-b') < names.index('package-c'), \
        f"package-b should come before package-c, got order: {names}"
    
    print(f"✓ Basic dependency order test passed: {names}")


def test_no_dependencies():
    """Test that packages without dependencies maintain stable order."""
    packages = [
        {'name': 'package-c', 'build_dependencies': []},
        {'name': 'package-a', 'build_dependencies': []},
        {'name': 'package-b', 'build_dependencies': []},
    ]
    
    sorted_packages = topological_sort(packages)
    names = [pkg['name'] for pkg in sorted_packages]
    
    # Should be alphabetically sorted when no dependencies
    assert names == ['package-a', 'package-b', 'package-c'], \
        f"Expected alphabetical order, got: {names}"
    
    print(f"✓ No dependencies test passed: {names}")


def test_complex_dependencies():
    """Test a more complex dependency graph."""
    packages = [
        {'name': 'app', 'build_dependencies': ['lib-a', 'lib-b']},
        {'name': 'lib-b', 'build_dependencies': ['core']},
        {'name': 'lib-a', 'build_dependencies': ['core']},
        {'name': 'core', 'build_dependencies': []},
        {'name': 'utils', 'build_dependencies': []},
    ]
    
    sorted_packages = topological_sort(packages)
    names = [pkg['name'] for pkg in sorted_packages]
    
    # core should come first
    assert names.index('core') < names.index('lib-a'), \
        f"core should come before lib-a, got order: {names}"
    assert names.index('core') < names.index('lib-b'), \
        f"core should come before lib-b, got order: {names}"
    
    # lib-a and lib-b should come before app
    assert names.index('lib-a') < names.index('app'), \
        f"lib-a should come before app, got order: {names}"
    assert names.index('lib-b') < names.index('app'), \
        f"lib-b should come before app, got order: {names}"
    
    # utils has no dependencies or dependents, so can be anywhere
    print(f"✓ Complex dependencies test passed: {names}")


def test_circular_dependency():
    """Test that circular dependencies are detected."""
    packages = [
        {'name': 'package-a', 'build_dependencies': ['package-b']},
        {'name': 'package-b', 'build_dependencies': ['package-a']},
    ]
    
    try:
        sorted_packages = topological_sort(packages)
        assert False, "Should have detected circular dependency"
    except SystemExit:
        print("✓ Circular dependency detection test passed")


def test_missing_dependency_warning():
    """Test that missing dependencies are handled gracefully."""
    packages = [
        {'name': 'package-a', 'build_dependencies': ['nonexistent']},
    ]
    
    # Should not crash, just print a warning
    sorted_packages = topological_sort(packages)
    print("✓ Missing dependency warning test passed")


def test_real_world_scenario():
    """Test with a realistic package dependency scenario."""
    packages = [
        {'name': 'cryptography', 'build_dependencies': ['cffi']},
        {'name': 'cffi', 'build_dependencies': []},
        {'name': 'pyyaml', 'build_dependencies': []},
        {'name': 'requests', 'build_dependencies': []},
    ]
    
    sorted_packages = topological_sort(packages)
    names = [pkg['name'] for pkg in sorted_packages]
    
    # cffi should come before cryptography
    assert names.index('cffi') < names.index('cryptography'), \
        f"cffi should come before cryptography, got order: {names}"
    
    print(f"✓ Real-world scenario test passed: {names}")


if __name__ == '__main__':
    print("="*60)
    print("Testing dependency resolution and build order")
    print("="*60)
    
    test_basic_dependency_order()
    test_no_dependencies()
    test_complex_dependencies()
    test_circular_dependency()
    test_missing_dependency_warning()
    test_real_world_scenario()
    
    print("\n" + "="*60)
    print("✓ All dependency resolution tests passed!")
    print("="*60)

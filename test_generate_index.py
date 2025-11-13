#!/usr/bin/env python3
"""
Test script for generate_index.py
Tests that packages with different capitalizations are kept separate.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Import the function we're testing
sys.path.insert(0, os.path.dirname(__file__))
from generate_index import get_package_name_from_wheel, generate_package_index, generate_root_index


def test_get_package_name_from_wheel():
    """Test that package names preserve case but normalize underscores."""
    print("Testing get_package_name_from_wheel()...")
    
    test_cases = [
        # (input_filename, expected_output)
        ("PyYAML-6.0-cp314-cp314-android_21_arm64_v8a.whl", "PyYAML"),
        ("pyyaml-6.0-cp314-cp314-android_21_arm64_v8a.whl", "pyyaml"),
        ("numpy-1.24.0-cp314-cp314-ios_arm64.whl", "numpy"),
        ("NumPy-1.24.0-cp314-cp314-ios_arm64.whl", "NumPy"),
        ("Some_Package-1.0-cp314-cp314-android.whl", "Some-Package"),
        ("some_package-1.0-cp314-cp314-android.whl", "some-package"),
        # Test hyphenated package names
        ("my-package-1.0.0-cp314-cp314-android.whl", "my-package"),
        ("some-hyphenated-name-2.1.0-cp314-cp314-android.whl", "some-hyphenated-name"),
        ("My-Hyphenated-Package-1.5.0-cp314-cp314-ios.whl", "My-Hyphenated-Package"),
    ]
    
    all_passed = True
    for wheel_filename, expected in test_cases:
        result = get_package_name_from_wheel(wheel_filename)
        if result == expected:
            print(f"  ✓ {wheel_filename} -> {result}")
        else:
            print(f"  ✗ {wheel_filename} -> {result} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_separate_case_packages():
    """Test that packages with different cases are kept separate in the index."""
    print("\nTesting separate indexes for different cases...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        wheels_dir = Path(tmpdir) / "wheels"
        output_dir = Path(tmpdir) / "output"
        wheels_dir.mkdir()
        
        # Create fake wheel files with different cases
        fake_wheels = [
            "PyYAML-6.0-cp314-cp314-android.whl",
            "pyyaml-6.0-cp314-cp314-android.whl",
        ]
        
        for wheel_name in fake_wheels:
            wheel_path = wheels_dir / wheel_name
            # Create a small fake wheel file
            wheel_path.write_bytes(b"fake wheel content")
        
        # Import and run the main generation logic
        from collections import defaultdict
        packages = defaultdict(list)
        
        for wheel_path in wheels_dir.glob('**/*.whl'):
            wheel_file = wheel_path.name
            package_name = get_package_name_from_wheel(wheel_file)
            
            if package_name:
                packages[package_name].append((wheel_file, wheel_path))
        
        # Check that we have TWO separate packages, not one merged
        if len(packages) == 2:
            print(f"  ✓ Found {len(packages)} separate packages (expected: 2)")
            for pkg_name in packages:
                print(f"    - {pkg_name}")
            return True
        else:
            print(f"  ✗ Found {len(packages)} packages (expected: 2)")
            for pkg_name in packages:
                print(f"    - {pkg_name}")
            return False


def main():
    print("=" * 60)
    print("Testing generate_index.py case sensitivity")
    print("=" * 60)
    
    test1_passed = test_get_package_name_from_wheel()
    test2_passed = test_separate_case_packages()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())

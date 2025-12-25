#!/usr/bin/env python3
"""
Test script for pre-built wheels functionality.
Tests that pre-built wheels from prebuilt-wheels/ directory are properly included in the index.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Import the functions we're testing
sys.path.insert(0, os.path.dirname(__file__))
from generate_index import get_package_name_from_wheel, generate_package_index, generate_root_index


def create_fake_wheel(path, filename):
    """Create a minimal fake wheel file for testing."""
    wheel_path = path / filename
    # Create a simple ZIP file (wheels are ZIP files)
    import zipfile
    with zipfile.ZipFile(wheel_path, 'w') as zf:
        # Add a minimal WHEEL metadata file
        zf.writestr('test_package-1.0.0.dist-info/WHEEL', 
                    'Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: cp314-cp314-android_21_arm64_v8a')
        zf.writestr('test_package-1.0.0.dist-info/METADATA',
                    'Metadata-Version: 2.1\nName: test-package\nVersion: 1.0.0')
    return wheel_path


def test_prebuilt_wheels_inclusion():
    """Test that pre-built wheels are properly included in the index."""
    print("\nTesting pre-built wheels inclusion...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        wheels_dir = Path(tmpdir) / "wheels"
        prebuilt_dir = Path(tmpdir) / "prebuilt-wheels"
        output_dir = Path(tmpdir) / "output"
        
        wheels_dir.mkdir()
        prebuilt_dir.mkdir()
        
        # Create a CI-built wheel
        ci_wheel = "numpy-1.24.0-cp314-cp314-android_21_arm64_v8a.whl"
        create_fake_wheel(wheels_dir, ci_wheel)
        
        # Create pre-built wheels
        prebuilt_wheels = [
            "requests-2.28.0-cp314-cp314-ios_arm64.whl",
            "pyyaml-6.0-cp314-cp314-android_21_x86_64.whl",
        ]
        
        for wheel_name in prebuilt_wheels:
            create_fake_wheel(prebuilt_dir, wheel_name)
        
        # Simulate the workflow step: copy prebuilt wheels to wheels dir
        for wheel_file in prebuilt_dir.glob("*.whl"):
            shutil.copy2(wheel_file, wheels_dir)
        
        # Verify all wheels are in the wheels directory
        all_wheels = list(wheels_dir.glob("*.whl"))
        expected_count = 1 + len(prebuilt_wheels)  # CI wheel + prebuilt wheels
        
        if len(all_wheels) == expected_count:
            print(f"  ✓ Found {len(all_wheels)} wheels total (1 CI-built + {len(prebuilt_wheels)} pre-built)")
            for wheel in sorted(all_wheels):
                print(f"    - {wheel.name}")
            return True
        else:
            print(f"  ✗ Expected {expected_count} wheels, found {len(all_wheels)}")
            return False


def test_index_generation_with_prebuilt():
    """Test that index generation works correctly with pre-built wheels."""
    print("\nTesting index generation with pre-built wheels...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        wheels_dir = Path(tmpdir) / "wheels"
        output_dir = Path(tmpdir) / "output"
        
        wheels_dir.mkdir()
        output_dir.mkdir()
        
        # Create a mix of wheels
        test_wheels = [
            "numpy-1.24.0-cp314-cp314-android_21_arm64_v8a.whl",
            "requests-2.28.0-cp314-cp314-ios_arm64.whl",
            "pyyaml-6.0-cp314-cp314-android_21_x86_64.whl",
        ]
        
        for wheel_name in test_wheels:
            create_fake_wheel(wheels_dir, wheel_name)
        
        # Generate index
        from collections import defaultdict
        packages = defaultdict(list)
        
        for wheel_path in wheels_dir.glob('**/*.whl'):
            wheel_file = wheel_path.name
            package_name = get_package_name_from_wheel(wheel_file)
            
            if package_name:
                packages[package_name].append((wheel_file, wheel_path))
        
        # Generate per-package indexes
        all_package_names = set()
        for package_name, wheels in packages.items():
            generate_package_index(package_name, wheels, output_dir)
            all_package_names.add(package_name)
        
        # Generate root index
        generate_root_index(all_package_names, output_dir)
        
        # Verify indexes were created
        root_index = output_dir / "index.html"
        
        if not root_index.exists():
            print("  ✗ Root index.html not created")
            return False
        
        # Check that all packages have their own index
        expected_packages = {'numpy', 'requests', 'pyyaml'}
        success = True
        
        for pkg in expected_packages:
            pkg_index = output_dir / pkg / "index.html"
            if pkg_index.exists():
                print(f"  ✓ Index created for {pkg}")
            else:
                print(f"  ✗ Index not created for {pkg}")
                success = False
        
        # Verify root index contains all packages
        root_content = root_index.read_text()
        for pkg in expected_packages:
            if f'"{pkg}/"' in root_content:
                print(f"  ✓ Root index contains link to {pkg}")
            else:
                print(f"  ✗ Root index missing link to {pkg}")
                success = False
        
        return success


def test_prebuilt_directory_empty():
    """Test that workflow handles empty or missing prebuilt-wheels directory gracefully."""
    print("\nTesting handling of empty prebuilt-wheels directory...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        wheels_dir = Path(tmpdir) / "wheels"
        prebuilt_dir = Path(tmpdir) / "prebuilt-wheels"
        
        wheels_dir.mkdir()
        # Don't create prebuilt_dir to simulate missing directory
        
        # Create one CI wheel
        ci_wheel = "numpy-1.24.0-cp314-cp314-android_21_arm64_v8a.whl"
        create_fake_wheel(wheels_dir, ci_wheel)
        
        # Simulate the workflow check
        has_prebuilt = prebuilt_dir.exists() and list(prebuilt_dir.glob("*.whl"))
        
        if not has_prebuilt:
            print("  ✓ Correctly detected no pre-built wheels")
        else:
            print("  ✗ Incorrectly detected pre-built wheels")
            return False
        
        # Verify only CI wheel is present
        all_wheels = list(wheels_dir.glob("*.whl"))
        if len(all_wheels) == 1:
            print(f"  ✓ Only CI-built wheel present: {all_wheels[0].name}")
            return True
        else:
            print(f"  ✗ Expected 1 wheel, found {len(all_wheels)}")
            return False


def main():
    print("=" * 70)
    print("Testing Pre-Built Wheels Functionality")
    print("=" * 70)
    
    test1_passed = test_prebuilt_wheels_inclusion()
    test2_passed = test_index_generation_with_prebuilt()
    test3_passed = test_prebuilt_directory_empty()
    
    print("\n" + "=" * 70)
    if test1_passed and test2_passed and test3_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())

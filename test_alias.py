#!/usr/bin/env python3
"""
Test script for alias functionality in generate_index.py
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Import the functions we're testing
sys.path.insert(0, os.path.dirname(__file__))
from generate_index import (
    get_package_name_from_wheel, 
    rename_wheel_for_alias,
    generate_package_index, 
    generate_root_index,
    main as generate_index_main
)


def test_rename_wheel_for_alias():
    """Test that wheel filenames are correctly renamed for aliases."""
    print("Testing rename_wheel_for_alias()...")
    
    test_cases = [
        # (wheel_filename, old_name, new_name, expected_output)
        ("PyYAML-6.0-cp314-cp314-android.whl", "PyYAML", "pyyaml", "pyyaml-6.0-cp314-cp314-android.whl"),
        ("pyyaml-6.0-cp314-cp314-android.whl", "pyyaml", "PyYAML", "PyYAML-6.0-cp314-cp314-android.whl"),
        ("numpy-1.24.0-cp314-cp314-ios.whl", "numpy", "NumPy", "NumPy-1.24.0-cp314-cp314-ios.whl"),
        # Test with underscores preserved
        ("Some_Package-1.0-cp314-cp314-android.whl", "Some-Package", "some-package", "some_package-1.0-cp314-cp314-android.whl"),
    ]
    
    all_passed = True
    for wheel_filename, old_name, new_name, expected in test_cases:
        result = rename_wheel_for_alias(wheel_filename, old_name, new_name)
        if result == expected:
            print(f"  ✓ {wheel_filename} ({old_name} -> {new_name}) => {result}")
        else:
            print(f"  ✗ {wheel_filename} ({old_name} -> {new_name}) => {result} (expected: {expected})")
            all_passed = False
    
    return all_passed


def test_alias_index_generation():
    """Test that indexes are correctly generated for both package name and alias."""
    print("\nTesting alias index generation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        wheels_dir = Path(tmpdir) / "wheels"
        output_dir = Path(tmpdir) / "output"
        metadata_file = Path(tmpdir) / "packages_metadata.json"
        
        wheels_dir.mkdir()
        
        # Create fake wheel file
        wheel_name = "PyYAML-6.0-cp314-cp314-android.whl"
        wheel_path = wheels_dir / wheel_name
        wheel_path.write_bytes(b"fake wheel content for testing")
        
        # Create package metadata with alias
        metadata = [
            {
                "spec": "pyyaml",
                "name": "pyyaml",
                "alias": "PyYAML",
                "source": "pypi"
            }
        ]
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Run generate_index with metadata
        original_argv = sys.argv
        try:
            sys.argv = ['generate_index.py', str(wheels_dir), str(output_dir), str(metadata_file)]
            generate_index_main()
        finally:
            sys.argv = original_argv
        
        # Check that both indexes were created
        pyyaml_index = output_dir / "pyyaml" / "index.html"
        PyYAML_index = output_dir / "PyYAML" / "index.html"
        
        if not pyyaml_index.exists():
            print(f"  ✗ Index not created for 'pyyaml'")
            return False
        
        if not PyYAML_index.exists():
            print(f"  ✗ Index not created for 'PyYAML'")
            return False
        
        # Check that wheel files exist with correct names
        pyyaml_wheel = output_dir / "pyyaml" / "pyyaml-6.0-cp314-cp314-android.whl"
        PyYAML_wheel = output_dir / "PyYAML" / "PyYAML-6.0-cp314-cp314-android.whl"
        
        if not pyyaml_wheel.exists():
            print(f"  ✗ Wheel file not created for 'pyyaml': {pyyaml_wheel}")
            return False
        
        if not PyYAML_wheel.exists():
            print(f"  ✗ Wheel file not created for 'PyYAML': {PyYAML_wheel}")
            return False
        
        # Check that both wheel files have the same content (SHA256)
        import hashlib
        
        def get_hash(filepath):
            hash_obj = hashlib.sha256()
            with open(filepath, 'rb') as f:
                hash_obj.update(f.read())
            return hash_obj.hexdigest()
        
        pyyaml_hash = get_hash(pyyaml_wheel)
        PyYAML_hash = get_hash(PyYAML_wheel)
        
        if pyyaml_hash != PyYAML_hash:
            print(f"  ✗ Wheel files have different hashes!")
            print(f"    pyyaml hash: {pyyaml_hash}")
            print(f"    PyYAML hash: {PyYAML_hash}")
            return False
        
        # Check that root index contains both packages
        root_index = output_dir / "index.html"
        root_content = root_index.read_text()
        
        if 'href="pyyaml/"' not in root_content:
            print(f"  ✗ Root index does not contain link to 'pyyaml'")
            return False
        
        if 'href="PyYAML/"' not in root_content:
            print(f"  ✗ Root index does not contain link to 'PyYAML'")
            return False
        
        # Check that index files contain correct wheel filenames
        pyyaml_index_content = pyyaml_index.read_text()
        PyYAML_index_content = PyYAML_index.read_text()
        
        if 'pyyaml-6.0-cp314-cp314-android.whl' not in pyyaml_index_content:
            print(f"  ✗ pyyaml index does not contain renamed wheel")
            return False
        
        if 'PyYAML-6.0-cp314-cp314-android.whl' not in PyYAML_index_content:
            print(f"  ✗ PyYAML index does not contain original wheel")
            return False
        
        print(f"  ✓ Both indexes created successfully")
        print(f"  ✓ Wheel files have matching hashes")
        print(f"  ✓ Root index contains both package names")
        print(f"  ✓ Wheel filenames correctly renamed in alias index")
        return True


def main():
    print("=" * 60)
    print("Testing alias functionality in generate_index.py")
    print("=" * 60)
    
    test1_passed = test_rename_wheel_for_alias()
    test2_passed = test_alias_index_generation()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ All alias tests passed!")
        return 0
    else:
        print("✗ Some alias tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())

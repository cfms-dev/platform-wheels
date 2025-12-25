# Pre-built Wheels Directory

This directory is for storing pre-built wheel files (.whl) that should be included in the package index.

## Usage

1. Place your pre-built .whl files directly in this directory
2. The workflow will automatically find and include them in the index during deployment
3. Pre-built wheels will be deployed alongside wheels built by the CI/CD pipeline

## Example Structure

```
prebuilt-wheels/
├── example_package-1.0.0-cp314-cp314-android_21_arm64_v8a.whl  # Example wheel (included)
├── another_package-2.1.0-cp314-cp314-ios_arm64.whl
└── README.md
```

## Example Wheel

This directory includes `example_package-1.0.0-cp314-cp314-android_21_arm64_v8a.whl` as a demonstration of the pre-built wheels feature. You can:
- Use it as a reference for wheel file structure
- Test the workflow with it
- Replace it with your own pre-built wheels

## Notes

- Wheels must be valid Python wheel files (`.whl` extension)
- Wheels must be compatible with Python 3.14 (cp314)
- Supported platforms: Android (arm64_v8a, x86_64) and iOS
- Wheel filenames must follow the standard wheel naming convention


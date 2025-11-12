# Platform Wheels Builder

This repository provides an automated system for building Python wheels for multiple platforms using [cibuildwheel](https://cibuildwheel.readthedocs.io/).

## Features

- Automated wheel building for Android and iOS platforms
- **Python 3.14 support** (officially released October 7th, 2025)
- Android builds for **arm64_v8a** and **x86_64** architectures (as specified)
- Easy package configuration via `packages.txt`
- Dynamic package list reading from configuration file
- Separate wheels for each package and platform combination

## Usage

### Adding Packages

Edit the `packages.txt` file to specify which Python packages to build. Add one package per line:

```
numpy==1.24.0
pandas
requests>=2.28.0
```

You can specify:
- Exact versions: `package==1.0.0`
- Minimum versions: `package>=1.0.0`
- Version ranges: `package>=1.0.0,<2.0.0`
- Just package names (latest version): `package`

Lines starting with `#` are treated as comments and ignored. Empty lines are also ignored.

See `packages.txt.example` for more examples.

### Triggering Builds

The workflow can be triggered in multiple ways:

1. **Manual trigger**: Go to Actions → Build → Run workflow
2. **Pull request**: Wheels are built when PRs are created/updated
3. **Push to main**: Wheels are built on every push to the main branch
4. **Release**: Wheels are built when a new release is published

### Built Wheels

After a successful build, wheel artifacts are available in:
- GitHub Actions artifacts (for manual/PR/push triggers)
- Release assets (for release triggers)

Each artifact is named: `cibw-wheels-{platform}-{package}`

## Platforms

### Android
- **arm64_v8a** (64-bit ARM)
- **x86_64** (64-bit Intel/AMD)

### iOS
- Default architectures for iOS

## Configuration

### Python Version
The build is configured for **Python 3.14** (cp314), which was officially released on October 7th, 2025.

### Build Environment Variables
The workflow uses these cibuildwheel environment variables:
- `CIBW_PLATFORM`: Specifies the target platform (android/ios)
- `CIBW_ARCHS`: Specifies the architecture(s) to build for
- `CIBW_BUILD`: Set to `cp314-*` to build only for Python 3.14

For advanced configuration, you can modify the `.github/workflows/wheels.yml` file.

## How It Works

1. The `read_packages` job reads the `packages.txt` file and parses the package list
2. The `build_wheels` job creates a matrix of all packages × platforms
3. For each combination:
   - Downloads the package source distribution
   - Extracts it
   - Uses cibuildwheel to build the wheel for the target platform
   - Uploads the built wheel as an artifact

## Requirements

- Packages must be available on PyPI or be installable via pip
- Packages must have proper `setup.py` or `pyproject.toml` for building
- Some packages may require additional build dependencies (configure in workflow if needed)

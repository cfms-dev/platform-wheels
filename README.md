# Platform Wheels Builder

This repository provides an automated system for building Python wheels for multiple platforms using [cibuildwheel](https://cibuildwheel.readthedocs.io/).

## Features

- Automated wheel building for Android and iOS platforms
- Support for Python 3.14
- Android builds for arm64_v8a and x86_64 architectures
- Easy package configuration via `packages.txt`

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
- Just package names (latest version): `package`

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

## Platforms

- **Android**: arm64_v8a, x86_64
- **iOS**: Default architectures for iOS

## Configuration

The build is configured for Python 3.14 and uses cibuildwheel for cross-platform wheel building.

For advanced configuration, you can modify the `.github/workflows/wheels.yml` file.

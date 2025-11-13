# Platform Wheels Builder

This repository provides an automated system for building Python wheels for multiple platforms using [cibuildwheel](https://cibuildwheel.readthedocs.io/).

## Features

- Automated wheel building for Android and iOS platforms
- **Python 3.14 support** (officially released October 7th, 2025)
- Android builds for **arm64_v8a** and **x86_64** architectures (as specified)
- Easy package configuration via `packages.txt` or advanced `packages.yaml`
- **Host dependency management** - Install system libraries needed by packages (e.g., libffi for cffi)
- **Custom source support** - Build from custom URLs or Git repositories
- **Patch support** - Apply patches to source code before building (e.g., mobile platform fixes)
- Dynamic package list reading from configuration file
- Separate wheels for each package and platform combination
- **Automatic deployment to GitHub Pages as a PyPI-like index**


## Usage

### Installing Wheels

After wheels are built and deployed, you can install them using pip with the extra index URL:

```bash
pip install --extra-index-url https://cfms-dev.github.io/platform-wheels/ <package-name>
```

For example:
```bash
pip install --extra-index-url https://cfms-dev.github.io/platform-wheels/ pyyaml
```

Or you can configure it in your `pip.conf` or `requirements.txt`:

**pip.conf:**
```ini
[global]
extra-index-url = https://cfms-dev.github.io/platform-wheels/
```

**requirements.txt:**
```
--extra-index-url https://cfms-dev.github.io/platform-wheels/
pyyaml
requests
```

### Adding Packages

You can configure packages in two ways:

#### Simple Configuration (packages.txt)

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

#### Advanced Configuration (packages.yaml)

For advanced features like host dependencies and custom sources, create a `packages.yaml` file:

```yaml
packages:
  # Simple package
  - name: requests

  # Package with version constraint
  - name: numpy
    version: "==1.24.0"

  # Package with host dependencies (e.g., cffi needs libffi)
  - name: cffi
    host_dependencies:
      - libffi-dev
    patches:
      - https://github.com/flet-dev/mobile-forge/raw/python3.12/recipes/cffi/patches/mobile.patch

  # Package with multiple host dependencies
  - name: cryptography
    host_dependencies:
      - libssl-dev
      - libffi-dev
      - cargo
      - rustc

  # Package from custom URL
  - name: custom-package
    source: url
    url: https://example.com/package.tar.gz

  # Package from Git repository
  - name: git-package
    source: git
    url: https://github.com/user/repo.git
```

**Supported options:**
- `name`: Package name (required)
- `version`: Version constraint (optional, e.g., `"==1.0.0"`, `">=2.0.0"`)
- `source`: Source type (optional: `pypi`, `url`, `git`; default: `pypi`)
- `url`: Custom URL for `url` or `git` sources (required if source is not `pypi`)
- `host_dependencies`: System packages to install before building (optional)
- `pip_dependencies`: Python packages needed for building (optional)
- `patches`: List of patch file URLs to apply to the source code (optional)

**Note:** If `packages.yaml` exists, it will be used. Otherwise, the system falls back to `packages.txt` for backward compatibility.

See `packages.yaml.example` for more examples.

### Triggering Builds

The workflow can be triggered in multiple ways:

1. **Manual trigger**: Go to Actions → Build → Run workflow
2. **Pull request**: Wheels are built when PRs are created/updated
3. **Push to main**: Wheels are built on every push to the main branch
4. **Release**: Wheels are built when a new release is published

### Built Wheels

After a successful build:
- **GitHub Actions artifacts**: Available for all workflow runs
- **GitHub Pages**: Deployed automatically on push to main or release (accessible via pip)
- **Release assets**: Attached to releases when triggered by a release event

Each artifact is named: `cibw-wheels-{platform}-{package}`

The wheel index is available at: https://cfms-dev.github.io/platform-wheels/

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

### GitHub Pages Setup

To enable wheel deployment, GitHub Pages must be configured in your repository:

1. Go to **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**
3. The workflow will automatically deploy the wheel index on push to main or release

The index will be available at: `https://<username>.github.io/<repository>/`

## How It Works

1. The `read_packages` job reads the `packages.txt` file and parses the package list
2. The `build_wheels` job creates a matrix of all packages × platforms
3. For each combination:
   - Installs required host dependencies (system libraries) if specified
   - Installs required pip dependencies if specified
   - Downloads the package source distribution (from PyPI, custom URL, or Git)
   - Extracts it
   - Uses cibuildwheel to build the wheel for the target platform
   - Uploads the built wheel as an artifact
4. The `deploy_index` job (on push to main or release):
   - Downloads all built wheel artifacts
   - Generates a PyPI-like HTML index structure
   - Deploys the index to GitHub Pages

### PyPI Index Structure

The generated index follows the simple repository API format used by pip:
- Root page (`/`) lists all available packages
- Each package has its own page (`/<package-name>/`) listing all available wheels
- Wheels include SHA256 hashes for verification

## Requirements

- Packages must be available on PyPI, accessible via URL, or in a Git repository
- Packages must have proper `setup.py` or `pyproject.toml` for building
- Host dependencies (system libraries) can be specified in `packages.yaml` if needed

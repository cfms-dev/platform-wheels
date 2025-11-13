# Platform Wheels Builder

This repository provides an automated system for building Python wheels for multiple platforms using [cibuildwheel](https://cibuildwheel.readthedocs.io/).

## Features

- Automated wheel building for Android and iOS platforms
- **Python 3.14 support** (officially released October 7th, 2025)
- Android builds for **arm64_v8a** and **x86_64** architectures (as specified)
- **Recipe-based configuration** - Organize packages with patches in `recipes/` directory
- Easy package configuration via `packages.txt`, `packages.yaml`, or `recipes/`
- **Host dependency management** - Install system libraries needed by packages (e.g., libffi for cffi)
- **Custom source support** - Build from custom URLs or Git repositories
- **Patch support** - Apply patches to source code before building (local files or URLs)
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

You can configure packages in three ways:

#### Recipe-based Configuration (recipes/)

**Recommended** for packages requiring special configuration. Create a directory under `recipes/` for each package:

```
recipes/
├── cffi/
│   ├── recipe.yaml
│   └── patches/
│       └── mobile.patch
└── cryptography/
    └── recipe.yaml
```

Example `recipes/cffi/recipe.yaml`:

```yaml
package:
  name: cffi

host_dependencies:
  - libffi-dev

patches:
  - patches/mobile.patch  # Local patch file
```

**Benefits:**
- Keeps patches organized with their packages
- Easy to maintain and version control
- Clear separation of concerns
- Patches stored locally in the repository

See `recipes/README.md` for detailed documentation.

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

For centralized configuration of multiple packages, create a `packages.yaml` file:

**Note:** Packages defined in `recipes/` take priority over `packages.yaml`.

```yaml
packages:
  # Simple package
  - name: requests

  # Package with version constraint
  - name: numpy
    version: "==1.24.0"

  # Package with alias (creates indexes for both names)
  # Useful when the PyPI package name differs from the desired index name
  - name: pyyaml
    alias: PyYAML

  # Package with host dependencies and external patch URL
  - name: some-package
    host_dependencies:
      - libffi-dev
    patches:
      - https://example.com/patches/fix.patch

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
- `alias`: Alternative package name for the index (optional). When specified, creates indexes for both the `name` and `alias` with appropriately renamed wheel files
- `source`: Source type (optional: `pypi`, `url`, `git`; default: `pypi`)
- `url`: Custom URL for `url` or `git` sources (required if source is not `pypi`)
- `host_dependencies`: System packages to install before building (optional). For cross-compilation, you should provide custom build scripts via `cibw_before_all` to compile these libraries for the target architecture
- `pip_dependencies`: Python packages needed for building (optional)
- `build_dependencies`: List of other packages that must be built first (optional). Useful when post-compilation tests require pre-built wheels of other packages
- `patches`: List of patch file URLs to apply to the source code (optional)

**Build Dependencies:**

The `build_dependencies` field allows you to specify that a package needs other packages to be built before it starts building. This is particularly useful when:
- Post-compilation tests require pre-built wheels of other packages
- A package needs to import/test against another package during its build process

Example:
```yaml
packages:
  - name: cffi
    host_dependencies:
      - libffi-dev

  - name: cryptography
    build_dependencies:
      - cffi  # Wait for cffi to build first
    host_dependencies:
      - libssl-dev
```

The build system will automatically:
1. Sort packages based on their dependencies (topological sort)
2. Build packages in the correct order
3. Wait for dependency wheels to be available before starting dependent builds
4. Install dependency wheels before building packages that depend on them

**Host Dependencies and Cross-Compilation:**

When specifying `host_dependencies`, you need to ensure these libraries are compiled for the target architecture (Android/iOS). The build system provides:

1. **Manual approach** (current, recommended): Create custom build scripts in `cibw_before_all` that cross-compile the libraries
   - Example: `recipes/cffi/build_libffi.sh` shows how to cross-compile libffi
   
2. **Automatic environment setup**: After your `cibw_before_all` script runs, the system automatically sources `scripts/setup_cross_compile_env.sh` which:
   - Searches for cross-compiled libraries in `/tmp/*-install-*` directories
   - Sets environment variables like `LIBFFI_INCLUDE_DIR`, `LIBFFI_LIB_DIR`, etc.
   - Adds library paths to `CFLAGS`, `LDFLAGS`, and `PKG_CONFIG_PATH`
   - Makes it easier for packages to discover cross-compiled dependencies

**Configuration Priority:**
1. `recipes/` directory (highest priority - recommended for packages with patches)
2. `packages.yaml` (for centralized configuration)
3. `packages.txt` (simple list, backward compatibility)

See `packages.yaml.example` and `recipes/README.md` for more examples.

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

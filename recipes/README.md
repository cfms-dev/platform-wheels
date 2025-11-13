# Package Recipes

This directory contains individual package recipes for packages that require special configuration, such as host dependencies, patches, or custom sources.

## Structure

Each package should have its own directory:

```
recipes/
├── cffi/
│   ├── recipe.yaml
│   └── patches/
│       └── mobile.patch
├── cryptography/
│   └── recipe.yaml
└── pillow/
    └── recipe.yaml
```

## Recipe Format

Each recipe is defined in a `recipe.yaml` file:

```yaml
# Recipe for package-name
package:
  name: package-name
  version: "==1.0.0"  # Optional: version constraint

# Optional: Source configuration
source: pypi  # or "url", "git"
url: https://example.com/package.tar.gz  # Required if source is "url" or "git"

# Optional: System packages needed for building
host_dependencies:
  - libffi-dev
  - libssl-dev

# Optional: Python packages needed for building
pip_dependencies:
  - setuptools
  - wheel

# Optional: Other packages that must be built first
# This ensures pre-built wheels are available for testing
build_dependencies:
  - cffi
  - numpy

# Optional: Patches to apply (can be URLs or local paths)
patches:
  - patches/fix-build.patch  # Local patch file (relative to recipe directory)
  - https://example.com/another.patch  # External patch URL

# Optional: cibuildwheel environment variables (for cross-compilation)
cibw_environment:
  PKG_CONFIG: ""  # Disable pkg-config
  CUSTOM_VAR: "value"

# Optional: Override cibuildwheel before_all script (empty string disables it)
cibw_before_all: ""  # Disable before_all script

# Optional: Override cibuildwheel config_settings
cibw_config_settings: "option1=value1 option2=value2"
```

## Local Patches

Store patch files in a `patches/` subdirectory within each recipe:

```
recipes/cffi/
├── recipe.yaml
└── patches/
    └── mobile.patch
```

In the recipe, reference patches relative to the recipe directory:

```yaml
patches:
  - patches/mobile.patch
```

## Examples

### Simple Package with Host Dependencies

```yaml
# recipes/cryptography/recipe.yaml
package:
  name: cryptography

host_dependencies:
  - libssl-dev
  - libffi-dev
  - cargo
  - rustc
```

### Package with Local Patch

```yaml
# recipes/cffi/recipe.yaml
package:
  name: cffi

host_dependencies:
  - libffi-dev

patches:
  - patches/mobile.patch
```

### Package from Custom URL

```yaml
# recipes/custom-lib/recipe.yaml
package:
  name: custom-lib

source: url
url: https://example.com/custom-lib-1.0.0.tar.gz

patches:
  - patches/fix-compilation.patch
```

### Package with Cross-Compilation Support (cffi example)

```yaml
# recipes/cffi/recipe.yaml
package:
  name: cffi

host_dependencies:
  - libffi-dev

# Disable pkg-config for Android/iOS cross-compilation
cibw_environment:
  PKG_CONFIG: ""

patches:
  - patches/mobile.patch  # Patch that disables system include dirs
```

### Package that Overrides cibuildwheel Config (pillow example)

```yaml
# recipes/pillow/recipe.yaml
package:
  name: pillow

# Disable before_all script that doesn't exist in PyPI sdist
cibw_before_all: ""

# Disable config settings that expect vendored libraries
cibw_config_settings: ""
```

## Cross-Compilation Notes

When building for Android/iOS:

1. **Host dependencies** installed via `apt-get` (Linux) or `brew` (macOS) provide libraries for the **build host** architecture (x86_64), not the **target** architecture (ARM64).

2. **For packages requiring native libraries** (like cffi requiring libffi):
   - Create a `cibw_before_all` script that cross-compiles the library for the target architecture
   - Use the Android NDK or iOS SDK toolchain
   - Install to a temporary location (e.g., `/tmp/libffi-install-arm64-v8a`)
   - Export environment variables (FFI_INCLUDE_DIR, FFI_LIB_DIR) for the package build

3. **Patches are essential** for packages that use pkg-config or system headers. The patch should:
   - Disable pkg-config detection
   - Remove hardcoded system include directories
   - Use environment variables (FFI_INCLUDE_DIR, FFI_LIB_DIR) if available
   - Allow the cross-compiler toolchain to find headers

4. **cibuildwheel environment overrides** help control the build:
   - `cibw_environment`: Set environment variables (e.g., disable PKG_CONFIG)
   - `cibw_before_all`: Build native dependencies for target architecture
   - `cibw_config_settings`: Control build-time configuration

5. **Example: cffi for Android/iOS**
   - Requires libffi compiled for target architecture
   - `cibw_before_all` script (`build_libffi.sh`) cross-compiles libffi using Android NDK
   - Exports FFI_INCLUDE_DIR and FFI_LIB_DIR pointing to cross-compiled libffi
   - Patch disables pkg-config and uses FFI_INCLUDE_DIR/FFI_LIB_DIR environment variables
   - Sets `PKG_CONFIG=""` to prevent finding host libraries
   - After custom build scripts run, `scripts/setup_cross_compile_env.sh` automatically:
     - Searches for cross-compiled libraries in common locations
     - Sets environment variables for discovered libraries
     - Adds paths to CFLAGS, LDFLAGS, and PKG_CONFIG_PATH
   
   See `recipes/cffi/` for a complete working example.

## Build Dependencies

The `build_dependencies` field allows you to specify that a package needs other packages to be built before it starts building. This is particularly useful when:
- Post-compilation tests require pre-built wheels of other packages
- A package needs to import/test against another package during its build process

Example:

```yaml
# recipes/package-with-tests/recipe.yaml
package:
  name: package-with-tests

build_dependencies:
  - cffi
  - numpy

# This package will:
# 1. Wait for cffi and numpy to finish building
# 2. Download and install their wheels before building
# 3. Can then import and test against these packages
```

The build system automatically:
1. Sorts all packages by their build dependencies (topological sort)
2. Builds packages in the correct order
3. Waits for dependency wheels to be available
4. Installs dependency wheels before building dependent packages
5. Detects circular dependencies and reports errors

## Priority

If a package is defined in both a recipe and `packages.yaml`, the recipe takes priority.

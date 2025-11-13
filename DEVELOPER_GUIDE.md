# Developer Guide: Build Dependencies and Host Dependencies

This guide explains how to use the build dependencies and host dependencies features in the Platform Wheels Builder.

## Table of Contents

1. [Build Dependencies](#build-dependencies)
2. [Host Dependencies](#host-dependencies)
3. [Complete Examples](#complete-examples)
4. [Troubleshooting](#troubleshooting)

## Build Dependencies

### What are Build Dependencies?

Build dependencies are other packages that must be built before your package can be built. This is useful when:

- Your package's post-compilation tests need to import other packages
- Your package needs to test against other packages during the build process
- Your package has integration tests that require pre-built wheels

### How to Use Build Dependencies

#### In recipe.yaml

```yaml
package:
  name: my-package

build_dependencies:
  - cffi
  - numpy
  - some-other-package
```

#### In packages.yaml

```yaml
packages:
  - name: my-package
    build_dependencies:
      - cffi
      - numpy
```

### How It Works

1. **Dependency Resolution**: When you run `read_packages.py`, it performs a topological sort on all packages based on their `build_dependencies`. This ensures packages are built in the correct order.

2. **Build Order**: Packages with no dependencies are built first, followed by packages that depend on them.

3. **Waiting for Dependencies**: During the build process, if a package has build dependencies:
   - The workflow waits for the dependency wheels to be uploaded as artifacts
   - It polls the GitHub API every 30 seconds for up to 30 minutes
   - Once available, it downloads and installs the dependency wheels
   - Then proceeds with building the current package

4. **Error Handling**: 
   - Circular dependencies are detected and reported as errors
   - Missing dependencies (not in the package list) generate warnings
   - Timeout waiting for dependencies causes the build to fail

### Important Notes

- Build dependencies must be packages defined in the same workflow (recipes or packages.yaml)
- For external Python dependencies from PyPI, use `pip_dependencies` instead
- Build dependencies are resolved per platform (Android/iOS builds are independent)

## Host Dependencies

### What are Host Dependencies?

Host dependencies are system libraries (like libffi, openssl, zlib) that need to be compiled for the target architecture before building your package. This is necessary for cross-compilation to Android/iOS.

### The Challenge

When building for Android/iOS, you're cross-compiling from x86_64 (build host) to ARM64 (target device). System libraries installed via `apt-get` or `brew` are compiled for the build host, not the target architecture.

### Solution: Two-Part Approach

#### Part 1: Custom Build Scripts (Required)

You need to provide a `cibw_before_all` script that cross-compiles your dependencies for the target architecture.

Example from `recipes/cffi/recipe.yaml`:

```yaml
package:
  name: cffi

host_dependencies:
  - libffi-dev

# Custom script that cross-compiles libffi
cibw_before_all: bash $GITHUB_WORKSPACE/recipes/cffi/build_libffi.sh

cibw_environment:
  PKG_CONFIG: ""  # Disable pkg-config to avoid finding host libraries
```

The `build_libffi.sh` script:
- Detects the target architecture from cibuildwheel environment variables
- Downloads libffi source code
- Cross-compiles it using Android NDK or iOS SDK toolchain
- Installs to a temporary location (e.g., `/tmp/libffi-install-arm64-v8a`)
- Exports environment variables for the package build

See `recipes/cffi/build_libffi.sh` for a complete example.

#### Part 2: Automatic Environment Setup (Provided)

After your custom script runs, the system automatically sources `scripts/setup_cross_compile_env.sh` which:

1. **Searches for libraries** in common locations:
   - `/tmp/<library>-install-*`
   - `/tmp/<library>-*`
   - `$HOME/.local/<library>`

2. **Sets environment variables** for discovered libraries:
   - `LIBFFI_INCLUDE_DIR` → `/tmp/libffi-install-arm64/include`
   - `LIBFFI_LIB_DIR` → `/tmp/libffi-install-arm64/lib`
   - Similar for other libraries (OPENSSL, ZLIB, etc.)

3. **Configures compiler flags**:
   - Adds `-I<include-dir>` to `CFLAGS` and `CPPFLAGS`
   - Adds `-L<lib-dir>` to `LDFLAGS`
   - Adds `<lib-dir>/pkgconfig` to `PKG_CONFIG_PATH`

### Using Environment Variables in Your Package

Your package's `setup.py` should check for these environment variables:

```python
import os

# Check for explicit environment variables first
include_dirs = []
library_dirs = []

if os.environ.get('FFI_INCLUDE_DIR'):
    include_dirs.append(os.environ['FFI_INCLUDE_DIR'])

if os.environ.get('FFI_LIB_DIR'):
    library_dirs.append(os.environ['FFI_LIB_DIR'])

# If not set, try to find cross-compiled library
if not include_dirs:
    import glob
    libffi_dirs = glob.glob('/tmp/libffi-install-*/include')
    if libffi_dirs:
        include_dirs.append(libffi_dirs[0])
        lib_dir = libffi_dirs[0].replace('/include', '/lib')
        if os.path.exists(lib_dir):
            library_dirs.append(lib_dir)
```

This is typically done via a patch file. See `recipes/cffi/patches/mobile.patch` for an example.

### Library Name Mapping

The environment setup script maps common package names to library names:

| Package Name | Library Name | Environment Variables |
|--------------|-------------|----------------------|
| libffi-dev | libffi | LIBFFI_INCLUDE_DIR, LIBFFI_LIB_DIR |
| libssl-dev | openssl | OPENSSL_INCLUDE_DIR, OPENSSL_LIB_DIR |
| zlib1g-dev | zlib | ZLIB_INCLUDE_DIR, ZLIB_LIB_DIR |
| libjpeg-dev | libjpeg | LIBJPEG_INCLUDE_DIR, LIBJPEG_LIB_DIR |
| libtiff-dev | libtiff | LIBTIFF_INCLUDE_DIR, LIBTIFF_LIB_DIR |

## Complete Examples

### Example 1: Package with Build Dependencies

```yaml
# recipes/cryptography/recipe.yaml
package:
  name: cryptography

# Wait for cffi to be built first
build_dependencies:
  - cffi

host_dependencies:
  - libssl-dev
  - libffi-dev
  - cargo
  - rustc
```

In this case:
1. cffi is built first (with its libffi dependency)
2. cryptography waits for cffi wheel to be available
3. cffi wheel is installed before building cryptography
4. cryptography can now import and test against cffi during build

### Example 2: Package with Host Dependencies and Custom Build Script

```yaml
# recipes/pillow/recipe.yaml
package:
  name: pillow

host_dependencies:
  - zlib1g-dev

# Custom script to build zlib, libjpeg, and libtiff for target architecture
cibw_before_all: |
  bash $GITHUB_WORKSPACE/recipes/pillow/build_zlib.sh
  bash $GITHUB_WORKSPACE/recipes/pillow/build_libjpeg.sh
  bash $GITHUB_WORKSPACE/recipes/pillow/build_libtiff.sh

cibw_environment:
  PKG_CONFIG: ""  # Disable pkg-config

# Patch to find cross-compiled libraries
patches:
  - patches/cross_compile_libs_detect.patch
```

The build scripts:
1. Cross-compile zlib, libjpeg, libtiff for target architecture
2. Install to `/tmp/zlib-install-arm64`, etc.
3. Environment setup script automatically finds them
4. Patch uses environment variables to locate libraries

### Example 3: Complex Package with Both Dependencies

```yaml
# recipes/complex-package/recipe.yaml
package:
  name: complex-package
  version: ">=1.0.0"

# Wait for these packages to be built first
build_dependencies:
  - cffi
  - pillow

# Need these system libraries
host_dependencies:
  - libffi-dev
  - libjpeg-dev

# Custom build script
cibw_before_all: |
  bash $GITHUB_WORKSPACE/recipes/complex-package/build_deps.sh

# Environment variables
cibw_environment:
  PKG_CONFIG: ""
  CUSTOM_FLAG: "value"

# Patches
patches:
  - patches/cross_compile.patch
```

## Troubleshooting

### Build Dependency Issues

**Problem**: "Timeout waiting for dependency X"

**Solutions**:
- Check if dependency X is in the package list
- Verify dependency X isn't failing to build
- Check if there's a circular dependency
- Look at the workflow logs for dependency X's build status

**Problem**: "Circular dependency detected among packages: A, B, C"

**Solutions**:
- Review your build_dependencies to find the cycle
- Remove unnecessary dependencies
- Consider if the dependency should be a pip_dependency instead

### Host Dependency Issues

**Problem**: "Library not found during build"

**Solutions**:
1. Verify your `cibw_before_all` script successfully built the library
2. Check if the library is installed to `/tmp/<library>-install-*`
3. Add debug output to see what environment variables are set:
   ```yaml
   cibw_before_all: |
     bash $GITHUB_WORKSPACE/recipes/mypackage/build_lib.sh
     echo "Environment variables:"
     env | grep -E "_(INCLUDE|LIB)_DIR" | sort
   ```
4. Verify your patch/setup.py checks for the environment variables

**Problem**: "Found host library instead of cross-compiled library"

**Solutions**:
- Set `PKG_CONFIG: ""` in `cibw_environment` to disable pkg-config
- Disable system include directories in your patch
- Make sure your setup.py checks environment variables first

### General Tips

1. **Test locally first**: Use the `read_packages.py` script to verify dependency order:
   ```bash
   python read_packages.py 2>&1 | grep "Found.*packages"
   ```

2. **Add debug output**: Add `echo` statements to your build scripts to see what's happening

3. **Check artifact names**: Build artifacts are named `cibw-wheels-<platform>-<package-name>`

4. **Review existing recipes**: Look at `recipes/cffi/` and `recipes/pillow/` for working examples

5. **Test dependency resolution**: Run `python test_dependencies.py` to verify your setup

## Additional Resources

- See `README.md` for general platform wheels documentation
- See `recipes/README.md` for recipe format documentation
- See `packages.yaml.example` for configuration examples
- Check `.github/workflows/wheels.yml` to understand the build process

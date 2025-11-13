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

# Optional: Patches to apply (can be URLs or local paths)
patches:
  - patches/fix-build.patch  # Local patch file (relative to recipe directory)
  - https://example.com/another.patch  # External patch URL
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

## Priority

If a package is defined in both a recipe and `packages.yaml`, the recipe takes priority.

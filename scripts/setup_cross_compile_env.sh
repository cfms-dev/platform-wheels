#!/bin/bash
# Central script to set up environment variables for cross-compiled host dependencies
# This makes it easier for packages to find cross-compiled libraries without individual patches

set -e

echo "Setting up cross-compilation environment for host dependencies..."

# Function to find a library installation in common locations
find_library_install() {
    local lib_name=$1
    local search_patterns=(
        "/tmp/${lib_name}-install-*"
        "/tmp/${lib_name}-*"
        "$HOME/.local/${lib_name}"
    )
    
    for pattern in "${search_patterns[@]}"; do
        # Use find to get the most recently modified directory
        local found=$(find $(dirname "$pattern") -maxdepth 1 -type d -name "$(basename "$pattern")" 2>/dev/null | sort -r | head -n 1)
        if [ -n "$found" ] && [ -d "$found" ]; then
            echo "$found"
            return 0
        fi
    done
    return 1
}

# Function to set up environment for a library
setup_library_env() {
    local lib_name=$1
    local lib_upper=$(echo "$lib_name" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
    
    echo "Looking for $lib_name..."
    
    local install_dir=$(find_library_install "$lib_name")
    if [ -z "$install_dir" ]; then
        echo "  ✗ $lib_name not found (skipping)"
        return 1
    fi
    
    echo "  ✓ Found at: $install_dir"
    
    # Set include directory
    if [ -d "$install_dir/include" ]; then
        export "${lib_upper}_INCLUDE_DIR=$install_dir/include"
        echo "  Set ${lib_upper}_INCLUDE_DIR=$install_dir/include"
        
        # Also add to CFLAGS/CPPFLAGS for general discovery
        export CFLAGS="${CFLAGS:-} -I$install_dir/include"
        export CPPFLAGS="${CPPFLAGS:-} -I$install_dir/include"
    fi
    
    # Set library directory
    for libdir in lib lib64 lib32; do
        if [ -d "$install_dir/$libdir" ]; then
            export "${lib_upper}_LIB_DIR=$install_dir/$libdir"
            echo "  Set ${lib_upper}_LIB_DIR=$install_dir/$libdir"
            
            # Also add to LDFLAGS for general discovery
            export LDFLAGS="${LDFLAGS:-} -L$install_dir/$libdir"
            break
        fi
    done
    
    # Set pkg-config path if available
    for pkgdir in lib/pkgconfig lib64/pkgconfig share/pkgconfig; do
        if [ -d "$install_dir/$pkgdir" ]; then
            export PKG_CONFIG_PATH="${PKG_CONFIG_PATH:-}:$install_dir/$pkgdir"
            echo "  Added to PKG_CONFIG_PATH: $install_dir/$pkgdir"
            break
        fi
    done
    
    return 0
}

# Map common library names to their actual names
# Format: library_name:search_name
declare -A LIBRARY_MAP=(
    ["libffi"]="libffi"
    ["libffi-dev"]="libffi"
    ["ffi"]="libffi"
    ["openssl"]="openssl"
    ["libssl"]="openssl"
    ["libssl-dev"]="openssl"
    ["ssl"]="openssl"
    ["zlib"]="zlib"
    ["zlib1g-dev"]="zlib"
    ["jpeg"]="libjpeg"
    ["libjpeg"]="libjpeg"
    ["libjpeg-dev"]="libjpeg"
    ["tiff"]="libtiff"
    ["libtiff"]="libtiff"
    ["libtiff-dev"]="libtiff"
    ["png"]="libpng"
    ["libpng"]="libpng"
    ["libpng-dev"]="libpng"
)

# Check if host dependencies are specified
if [ -n "$HOST_DEPENDENCIES" ]; then
    echo "Host dependencies specified: $HOST_DEPENDENCIES"
    
    # Process each dependency
    for dep in $HOST_DEPENDENCIES; do
        # Skip system tools that don't need library paths
        case "$dep" in
            cargo|rustc|gcc|g++|make|cmake|ninja*)
                echo "  Skipping system tool: $dep"
                continue
                ;;
        esac
        
        # Map dependency name to library name
        lib_search_name="${LIBRARY_MAP[$dep]:-$dep}"
        
        # Set up environment for this library
        setup_library_env "$lib_search_name"
    done
else
    echo "No host dependencies specified (HOST_DEPENDENCIES not set)"
fi

# Export all environment variables for subprocesses
export CFLAGS CPPFLAGS LDFLAGS PKG_CONFIG_PATH

echo ""
echo "Cross-compilation environment setup complete!"
echo "Environment variables set:"
env | grep -E "_(INCLUDE|LIB)_DIR|CFLAGS|CPPFLAGS|LDFLAGS|PKG_CONFIG_PATH" | sort || true

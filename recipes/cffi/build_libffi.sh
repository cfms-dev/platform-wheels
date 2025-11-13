#!/bin/bash
# Build libffi for Android/iOS cross-compilation
# This script is called by cibuildwheel before building cffi

set -e

echo "Building libffi for cross-compilation..."

# Detect platform
if [ "$CIBW_PLATFORM" = "android" ]; then
    echo "Building libffi for Android..."
    
    # Get Android NDK path (cibuildwheel sets this up)
    if [ -z "$ANDROID_NDK_ROOT" ] && [ -n "$ANDROID_NDK_HOME" ]; then
        ANDROID_NDK_ROOT="$ANDROID_NDK_HOME"
    fi
    
    if [ -z "$ANDROID_NDK_ROOT" ]; then
        echo "Error: ANDROID_NDK_ROOT not set"
        exit 1
    fi
    
    echo "Using Android NDK: $ANDROID_NDK_ROOT"
    
    # Determine target architecture
    case "$CIBW_ARCHS" in
        arm64_v8a|aarch64)
            TARGET_ARCH="aarch64"
            ANDROID_ABI="arm64-v8a"
            ;;
        x86_64)
            TARGET_ARCH="x86_64"
            ANDROID_ABI="x86_64"
            ;;
        armeabi-v7a|armv7)
            TARGET_ARCH="armv7a"
            ANDROID_ABI="armeabi-v7a"
            ;;
        x86)
            TARGET_ARCH="i686"
            ANDROID_ABI="x86"
            ;;
        *)
            echo "Unsupported architecture: $CIBW_ARCHS"
            exit 1
            ;;
    esac
    
    echo "Building for architecture: $TARGET_ARCH ($ANDROID_ABI)"
    
    # Set Android API level (minimum supported by Python mobile builds)
    ANDROID_API_LEVEL=${ANDROID_API_LEVEL:-21}
    
    # Download libffi source
    LIBFFI_VERSION="3.4.6"
    LIBFFI_DIR="/tmp/libffi-${LIBFFI_VERSION}"
    
    if [ ! -d "$LIBFFI_DIR" ]; then
        cd /tmp
        curl -L -o libffi.tar.gz "https://github.com/libffi/libffi/releases/download/v${LIBFFI_VERSION}/libffi-${LIBFFI_VERSION}.tar.gz"
        tar -xzf libffi.tar.gz
        rm libffi.tar.gz
    fi
    
    cd "$LIBFFI_DIR"
    
    # Set up NDK toolchain
    TOOLCHAIN="$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64"
    
    # Configure compiler and flags
    case "$TARGET_ARCH" in
        aarch64)
            HOST="aarch64-linux-android"
            ;;
        x86_64)
            HOST="x86_64-linux-android"
            ;;
        armv7a)
            HOST="armv7a-linux-androideabi"
            ;;
        i686)
            HOST="i686-linux-android"
            ;;
    esac
    
    export CC="$TOOLCHAIN/bin/${HOST}${ANDROID_API_LEVEL}-clang"
    export CXX="$TOOLCHAIN/bin/${HOST}${ANDROID_API_LEVEL}-clang++"
    export AR="$TOOLCHAIN/bin/llvm-ar"
    export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
    export STRIP="$TOOLCHAIN/bin/llvm-strip"
    
    # Set install prefix
    PREFIX="/tmp/libffi-install-${ANDROID_ABI}"
    
    # Clean and configure
    make clean || true
    
    ./configure \
        --host="$HOST" \
        --prefix="$PREFIX" \
        --enable-static \
        --disable-shared \
        --disable-dependency-tracking \
        --disable-builddir
    
    # Build and install
    make -j$(nproc)
    make install
    
    echo "libffi built and installed to: $PREFIX"
    ls -la "$PREFIX/include" || true
    ls -la "$PREFIX/lib" || true
    
    # Export environment variables for cffi to find libffi
    # These will be available to the build process
    export FFI_INCLUDE_DIR="$PREFIX/include"
    export FFI_LIB_DIR="$PREFIX/lib"
    
    echo "Environment variables set:"
    echo "  FFI_INCLUDE_DIR=$FFI_INCLUDE_DIR"
    echo "  FFI_LIB_DIR=$FFI_LIB_DIR"
    
    echo "libffi build complete for Android $ANDROID_ABI"
    
elif [ "$CIBW_PLATFORM" = "ios" ]; then
    echo "Building libffi for iOS..."
    
    # For iOS, libffi might be provided by the system or we need a similar approach
    # iOS cross-compilation is more complex and may require xcframework
    
    # Download libffi source
    LIBFFI_VERSION="3.4.6"
    LIBFFI_DIR="/tmp/libffi-${LIBFFI_VERSION}"
    
    if [ ! -d "$LIBFFI_DIR" ]; then
        cd /tmp
        curl -L -o libffi.tar.gz "https://github.com/libffi/libffi/releases/download/v${LIBFFI_VERSION}/libffi-${LIBFFI_VERSION}.tar.gz"
        tar -xzf libffi.tar.gz
        rm libffi.tar.gz
    fi
    
    cd "$LIBFFI_DIR"
    
    # Set install prefix
    PREFIX="/tmp/libffi-install-ios"
    
    # For iOS, we need to build for the simulator or device
    # This is a simplified version - full iOS support would need more work
    ./configure \
        --prefix="$PREFIX" \
        --enable-static \
        --disable-shared
    
    make -j$(sysctl -n hw.ncpu)
    make install
    
    echo "libffi built and installed to: $PREFIX"
    ls -la "$PREFIX/include" || true
    ls -la "$PREFIX/lib" || true
    
    # Export environment variables
    export FFI_INCLUDE_DIR="$PREFIX/include"
    export FFI_LIB_DIR="$PREFIX/lib"
    
    echo "Environment variables set:"
    echo "  FFI_INCLUDE_DIR=$FFI_INCLUDE_DIR"
    echo "  FFI_LIB_DIR=$FFI_LIB_DIR"
    
    echo "libffi build complete for iOS"
else
    echo "Platform $CIBW_PLATFORM not supported for libffi cross-build"
    exit 1
fi

echo "libffi cross-compilation setup complete"

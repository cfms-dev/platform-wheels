#!/bin/bash
# Build libjpeg-turbo for Android/iOS cross-compilation
# This script is called by cibuildwheel before building pillow

set -e

echo "Building libjpeg-turbo for cross-compilation..."

# Detect platform
if [ "$CIBW_PLATFORM" = "android" ]; then
    echo "Building libjpeg-turbo for Android..."
    
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
    
    # Set Android API level
    ANDROID_API_LEVEL=${ANDROID_API_LEVEL:-21}
    
    # Download libjpeg-turbo source
    LIBJPEG_VERSION="3.0.1"
    LIBJPEG_DIR="/tmp/libjpeg-turbo-${LIBJPEG_VERSION}"
    
    if [ ! -d "$LIBJPEG_DIR" ]; then
        cd /tmp
        curl -L -o libjpeg-turbo.tar.gz "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/${LIBJPEG_VERSION}/libjpeg-turbo-${LIBJPEG_VERSION}.tar.gz"
        tar -xzf libjpeg-turbo.tar.gz
        rm libjpeg-turbo.tar.gz
    fi
    
    cd "$LIBJPEG_DIR"
    
    # Set up NDK toolchain
    TOOLCHAIN="$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64"
    
    # Configure compiler and flags
    case "$TARGET_ARCH" in
        aarch64)
            HOST="aarch64-linux-android"
            CMAKE_SYSTEM_PROCESSOR="aarch64"
            ;;
        x86_64)
            HOST="x86_64-linux-android"
            CMAKE_SYSTEM_PROCESSOR="x86_64"
            ;;
        armv7a)
            HOST="armv7a-linux-androideabi"
            CMAKE_SYSTEM_PROCESSOR="armv7-a"
            ;;
        i686)
            HOST="i686-linux-android"
            CMAKE_SYSTEM_PROCESSOR="i686"
            ;;
    esac
    
    # Set compiler paths
    export CC="$TOOLCHAIN/bin/${HOST}${ANDROID_API_LEVEL}-clang"
    export CXX="$TOOLCHAIN/bin/${HOST}${ANDROID_API_LEVEL}-clang++"
    export AR="$TOOLCHAIN/bin/llvm-ar"
    export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
    export STRIP="$TOOLCHAIN/bin/llvm-strip"
    
    # Explicitly set sysroot to avoid using host system headers
    SYSROOT="$TOOLCHAIN/sysroot"
    export CFLAGS="--sysroot=$SYSROOT -fPIC"
    export CXXFLAGS="--sysroot=$SYSROOT"
    export LDFLAGS="--sysroot=$SYSROOT"
    
    # Configure and build libjpeg-turbo using CMake
    INSTALL_DIR="/tmp/libjpeg-install-${ANDROID_ABI}"
    BUILD_DIR="build-${ANDROID_ABI}"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Configure with CMake for Android
    cmake .. \
        -DCMAKE_SYSTEM_NAME=Android \
        -DCMAKE_SYSTEM_VERSION=${ANDROID_API_LEVEL} \
        -DCMAKE_ANDROID_ARCH_ABI=${ANDROID_ABI} \
        -DCMAKE_ANDROID_NDK=${ANDROID_NDK_ROOT} \
        -DCMAKE_C_COMPILER=${CC} \
        -DCMAKE_CXX_COMPILER=${CXX} \
        -DCMAKE_AR=${AR} \
        -DCMAKE_RANLIB=${RANLIB} \
        -DCMAKE_STRIP=${STRIP} \
        -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_SHARED=OFF \
        -DENABLE_STATIC=ON \
        -DWITH_TURBOJPEG=OFF
    
    # Build
    make -j$(nproc)
    make install
    
    echo "libjpeg-turbo build complete for Android $ANDROID_ABI"
    echo "Installed to: $INSTALL_DIR"
    echo "  Headers: $INSTALL_DIR/include"
    echo "  Library: $INSTALL_DIR/lib"

elif [ "$CIBW_PLATFORM" = "ios" ]; then
    echo "Building libjpeg-turbo for iOS..."
    
    # Detect iOS SDK
    if [ -n "$IPHONEOS_DEPLOYMENT_TARGET" ]; then
        # Building for device
        SDK_NAME="iphoneos"
    else
        # Building for simulator
        SDK_NAME="iphonesimulator"
    fi
    
    SDK_PATH=$(xcrun --sdk "$SDK_NAME" --show-sdk-path)
    echo "Using SDK: $SDK_NAME at $SDK_PATH"
    
    # Determine architecture
    if [ "$CIBW_ARCHS" = "all" ]; then
        echo "Building all iOS architectures (arm64 and x86_64)"
        for ARCH in arm64 x86_64; do
            echo "Starting sub-build for: $ARCH"
            CIBW_ARCHS="$ARCH" bash "$0"
        done
        exit 0
    fi
    
    case "$CIBW_ARCHS" in
        arm64)
            if [ "$SDK_NAME" = "iphoneos" ]; then
                # Device (iPhone/iPad)
                TARGET_ARCH="arm64"
                HOST="aarch64-apple-darwin"
            else
                # M1 simulator
                TARGET_ARCH="arm64"
                HOST="aarch64-apple-darwin"
            fi
            ;;
        x86_64)
            # Intel simulator
            TARGET_ARCH="x86_64"
            HOST="x86_64-apple-darwin"
            ;;
        *)
            echo "Unsupported iOS architecture: $CIBW_ARCHS"
            exit 1
            ;;
    esac
    
    echo "Building for architecture: $TARGET_ARCH"
    
    # Download libjpeg-turbo source
    LIBJPEG_VERSION="3.0.1"
    LIBJPEG_DIR="/tmp/libjpeg-turbo-${LIBJPEG_VERSION}"
    
    if [ ! -d "$LIBJPEG_DIR" ]; then
        cd /tmp
        curl -L -o libjpeg-turbo.tar.gz "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/${LIBJPEG_VERSION}/libjpeg-turbo-${LIBJPEG_VERSION}.tar.gz"
        tar -xzf libjpeg-turbo.tar.gz
        rm libjpeg-turbo.tar.gz
    fi
    
    cd "$LIBJPEG_DIR"
    
    # Set minimum iOS version
    MIN_IOS_VERSION="12.0"
    
    # Set compiler and flags
    export CC="$(xcrun --find clang)"
    export CXX="$(xcrun --find clang++)"
    export CFLAGS="-arch $TARGET_ARCH -isysroot $SDK_PATH -mios-version-min=$MIN_IOS_VERSION -fPIC"
    export CXXFLAGS="$CFLAGS"
    export LDFLAGS="-arch $TARGET_ARCH -isysroot $SDK_PATH"
    
    # Configure and build
    INSTALL_DIR="/tmp/libjpeg-install-${TARGET_ARCH}"
    BUILD_DIR="build-${TARGET_ARCH}"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Configure with CMake for iOS
    cmake .. \
        -DCMAKE_SYSTEM_NAME=iOS \
        -DCMAKE_OSX_ARCHITECTURES=${TARGET_ARCH} \
        -DCMAKE_OSX_DEPLOYMENT_TARGET=${MIN_IOS_VERSION} \
        -DCMAKE_OSX_SYSROOT=${SDK_PATH} \
        -DCMAKE_C_COMPILER=${CC} \
        -DCMAKE_CXX_COMPILER=${CXX} \
        -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
        -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_SHARED=OFF \
        -DENABLE_STATIC=ON \
        -DWITH_TURBOJPEG=OFF
    
    # Build
    make -j$(sysctl -n hw.ncpu)
    make install
    
    echo "libjpeg-turbo build complete for iOS $TARGET_ARCH"
    echo "Installed to: $INSTALL_DIR"
    echo "  Headers: $INSTALL_DIR/include"
    echo "  Library: $INSTALL_DIR/lib"
else
    echo "Unsupported platform: $CIBW_PLATFORM"
    exit 1
fi

echo "libjpeg-turbo cross-compilation complete"

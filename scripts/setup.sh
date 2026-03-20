#!/bin/bash
set -e

PACKAGES=(
    build-essential nasm
    python3-dev cython3
    qemu-system-x86 qemu-system-arm qemu-system-riscv64
    gcc-x86-64-linux-gnu gcc-aarch64-linux-gnu gcc-riscv64-linux-gnu
    binutils-x86-64-linux-gnu binutils-aarch64-linux-gnu binutils-riscv64-linux-gnu
    gdb
)

error_handler() {
    echo "[ERROR] An error occurred on line $1."
    exit 1
}
trap 'error_handler $LINENO' ERR

check_requirements() {
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "[ERROR] This script requires a Debian/Ubuntu-based system with apt-get."
        exit 1
    fi
}

install_deps() {
    echo "Installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y "${PACKAGES[@]}"
    echo "Dependencies installed successfully."
}

uninstall_deps() {
    echo "WARNING: This will uninstall the following packages from your system:"
    echo "${PACKAGES[@]}"
    echo "Note: Packages like 'build-essential' and 'python3-dev' might be used by other projects."
    read -p "Are you sure you want to proceed? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo "Uninstalling dependencies..."
        sudo apt-get remove --purge -y "${PACKAGES[@]}"
        sudo apt-get autoremove -y
        echo "Dependencies uninstalled successfully."
    else
        echo "Uninstallation cancelled."
    fi
}

check_requirements

if [ "$1" == "uninstall" ] || [ "$1" == "--uninstall" ]; then
    uninstall_deps
elif [ -z "$1" ] || [ "$1" == "install" ]; then
    install_deps
else
    echo "Usage: $0 [install|uninstall]"
    exit 1
fi

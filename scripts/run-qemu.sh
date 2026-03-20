#!/bin/bash

set -e

ARCH=$1
KERNEL_TARGET=${KERNEL_TARGET:-kernel-$ARCH}
ISO_NAME=${ISO_NAME:-os-$ARCH}
UEFI_DISK_NAME=${UEFI_DISK_NAME:-}

if [ -z "$ARCH" ]; then
    echo "Usage: $0 <architecture>"
    echo "Supported architectures: x86_64, aarch64, riscv64"
    exit 1
fi

QEMU_OPTS="-serial mon:stdio"
HEADLESS_OPTS="-nographic"
RUN_HEADLESS=${HEADLESS:-1}

NET_OPTS=""
if [ "${ENABLE_NET:-0}" = "1" ]; then
    NET_OPTS="-netdev user,id=net0,hostfwd=tcp::2222-:22 -device virtio-net-pci,netdev=net0"
fi

echo "Booting $ARCH kernel in QEMU..."

case $ARCH in
    x86_64)
        ISO="build/$ISO_NAME.iso"
        UEFI_DISK=""
        if [ -n "$UEFI_DISK_NAME" ] && [ -f "build/$UEFI_DISK_NAME.img" ]; then
            UEFI_DISK="build/$UEFI_DISK_NAME.img"
        fi
        OVMF_FW=""
        for candidate in /usr/share/ovmf/OVMF.fd /usr/share/qemu/OVMF.fd /usr/share/OVMF/OVMF_CODE_4M.fd; do
            if [ -f "$candidate" ]; then
                OVMF_FW="$candidate"
                break
            fi
        done
        if [ -z "$OVMF_FW" ]; then
            echo "UEFI firmware not found. Install OVMF to boot the generated GRUB ISO."
            exit 1
        fi
        if [ -n "$UEFI_DISK" ]; then
            if [ "$RUN_HEADLESS" = "1" ]; then
                qemu-system-x86_64 -bios "$OVMF_FW" -drive format=raw,file="$UEFI_DISK" $QEMU_OPTS $HEADLESS_OPTS $NET_OPTS
            else
                qemu-system-x86_64 -bios "$OVMF_FW" -drive format=raw,file="$UEFI_DISK" $QEMU_OPTS $NET_OPTS
            fi
        elif [ -f "$ISO" ]; then
            if [ "$RUN_HEADLESS" = "1" ]; then
                qemu-system-x86_64 -bios "$OVMF_FW" -cdrom "$ISO" $QEMU_OPTS $HEADLESS_OPTS $NET_OPTS
            else
                qemu-system-x86_64 -bios "$OVMF_FW" -cdrom "$ISO" $QEMU_OPTS $NET_OPTS
            fi
        else
            echo "No bootable x86_64 image found."
            echo "Build with 'make run' for the UEFI path or 'make run-grub' for the GRUB fallback."
            exit 1
        fi
        ;;
    aarch64)
        KERNEL="build/$KERNEL_TARGET.bin"
        if [ ! -f "$KERNEL" ]; then
            echo "Kernel file not found: $KERNEL"
            echo "Please build the kernel first with 'make ARCH=$ARCH'"
            exit 1
        fi
        qemu-system-aarch64 -M virt -cpu cortex-a53 -kernel "$KERNEL" $QEMU_OPTS $HEADLESS_OPTS $NET_OPTS
        ;;
    riscv64)
        KERNEL="build/$KERNEL_TARGET.bin"
        if [ ! -f "$KERNEL" ]; then
            echo "Kernel file not found: $KERNEL"
            echo "Please build the kernel first with 'make ARCH=$ARCH'"
            exit 1
        fi
        qemu-system-riscv64 -M virt -kernel "$KERNEL" $QEMU_OPTS $HEADLESS_OPTS $NET_OPTS
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

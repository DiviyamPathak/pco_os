#!/bin/bash

set -e

ARCH=$1
KERNEL_TARGET=${KERNEL_TARGET:-kernel-$ARCH}
ISO_NAME=${ISO_NAME:-os-$ARCH}
UEFI_DISK_NAME=${UEFI_DISK_NAME:-}
GDB_BIN=${GDB_BIN:-gdb}

if [ -z "$ARCH" ]; then
    echo "Usage: $0 <architecture>"
    echo "Supported architectures: x86_64"
    exit 1
fi

KERNEL="build/$KERNEL_TARGET.elf"
ISO="build/$ISO_NAME.iso"
UEFI_DISK="build/$UEFI_DISK_NAME.img"
OVMF_FW=""

if [ ! -f "$KERNEL" ]; then
    echo "Kernel file not found: $KERNEL"
    echo "Please build the kernel first with 'make ARCH=$ARCH'"
    exit 1
fi

if [ ! -f "$ISO" ] && [ ! -f "$UEFI_DISK" ]; then
    echo "ISO file not found: $ISO"
    echo "Please build the kernel first with 'make ARCH=$ARCH debug'"
    exit 1
fi

for candidate in /usr/share/ovmf/OVMF.fd /usr/share/qemu/OVMF.fd /usr/share/OVMF/OVMF_CODE_4M.fd; do
    if [ -f "$candidate" ]; then
        OVMF_FW="$candidate"
        break
    fi
done

if [ -z "$OVMF_FW" ]; then
    echo "UEFI firmware not found. Install OVMF to debug the generated GRUB ISO."
    exit 1
fi

if [ -f "$UEFI_DISK" ]; then
    qemu-system-x86_64 \
        -bios "$OVMF_FW" \
        -drive format=raw,file="$UEFI_DISK" \
        -serial mon:stdio \
        -nographic \
        -s \
        -S &
else
    qemu-system-x86_64 \
        -bios "$OVMF_FW" \
        -cdrom "$ISO" \
        -serial mon:stdio \
        -nographic \
        -s \
        -S &
fi
QEMU_PID=$!

trap 'kill $QEMU_PID' EXIT

"$GDB_BIN" \
    -ex "target remote localhost:1234" \
    -ex "symbol-file $KERNEL" \
    -ex "layout src" \
    -ex "break kernel_main"

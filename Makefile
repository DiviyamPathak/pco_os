# Makefile for PCO OS (Codon Edition)

# Default architecture
ARCH ?= x86_64

# Toolchain
CODON = /home/helmhotz/.codon/bin/codon
LLC = llc
AS = nasm
LD = ld
CC = gcc
OBJCOPY = objcopy
PYTHON = python3

# Directories
ARCH_DIR = src/arch/$(ARCH)
BOOT_DIR = src/boot
UEFI_SRC_DIR = $(BOOT_DIR)/uefi
GRUB_SRC_DIR = $(BOOT_DIR)/grub
KERNEL_DIR = src/kernel
USER_DIR = src/user
INITRAMFS_DIR = initramfs
BUILD_DIR = build
PROJECT_NAME ?= $(notdir $(CURDIR))

# --- Source Files ---
BOOT_SRC = $(ARCH_DIR)/boot.s
RUNTIME_SRC = $(ARCH_DIR)/runtime.s
INTERRUPTS_SRC = $(ARCH_DIR)/interrupts.s
KERNEL_SRC = $(KERNEL_DIR)/kernel.py
KERNEL_PY_SRCS = $(wildcard $(KERNEL_DIR)/*.py)
USER_SRCS = $(wildcard $(USER_DIR)/*.s) $(USER_DIR)/linker.ld
INITRAMFS_SRCS = $(shell find $(INITRAMFS_DIR) -type f 2>/dev/null | sort)
EFI_LOADER_SRC = $(UEFI_SRC_DIR)/efi_loader.c
EFI_ENTRY_SRC = $(UEFI_SRC_DIR)/efi_entry.S
GRUB_CFG = $(GRUB_SRC_DIR)/grub.cfg

BOOT_NAME = $(notdir $(basename $(BOOT_SRC)))
RUNTIME_NAME = $(notdir $(basename $(RUNTIME_SRC)))
INTERRUPTS_NAME = $(notdir $(basename $(INTERRUPTS_SRC)))
KERNEL_NAME = $(notdir $(basename $(KERNEL_SRC)))
EFI_LOADER_NAME = $(notdir $(basename $(EFI_LOADER_SRC)))
EFI_ENTRY_NAME = $(notdir $(basename $(EFI_ENTRY_SRC)))
KERNEL_TARGET = $(KERNEL_NAME)-$(ARCH)
ISO_NAME = $(PROJECT_NAME)-$(ARCH)
UEFI_DISK_NAME = $(PROJECT_NAME)-$(ARCH)-uefi

# --- Intermediate Files ---
KERNEL_LL = $(BUILD_DIR)/$(KERNEL_NAME).ll
BOOT_OBJ = $(BUILD_DIR)/$(BOOT_NAME).o
RUNTIME_OBJ = $(BUILD_DIR)/$(RUNTIME_NAME).o
INTERRUPTS_OBJ = $(BUILD_DIR)/$(INTERRUPTS_NAME).o
KERNEL_OBJ = $(BUILD_DIR)/$(KERNEL_NAME).o
EFI_LOADER_OBJ = $(BUILD_DIR)/$(EFI_LOADER_NAME).o
EFI_ENTRY_OBJ = $(BUILD_DIR)/$(EFI_ENTRY_NAME).o
OBJS = $(BOOT_OBJ) $(RUNTIME_OBJ) $(INTERRUPTS_OBJ) $(KERNEL_OBJ)

# --- Final Binary ---
KERNEL_ELF = $(BUILD_DIR)/$(KERNEL_TARGET).elf
KERNEL_IMAGE = $(notdir $(KERNEL_ELF))

# --- Compiler and Linker Flags ---
ASFLAGS = -f elf64
LDFLAGS = -m elf_x86_64 --gc-sections
LDSCRIPT = $(ARCH_DIR)/linker.ld
EFI_CFLAGS = -ffreestanding -fshort-wchar -mno-red-zone -maccumulate-outgoing-args -mno-sse -mno-sse2 -mgeneral-regs-only -fcf-protection=none -fno-stack-protector -fno-asynchronous-unwind-tables -fno-unwind-tables -fno-ident -fno-pic -fno-pie -fno-builtin -Wall -Wextra -Wno-unused-parameter
EFI_LDFLAGS = -mi386pep --subsystem 10 --entry efi_entry --image-base 0x10000000
LLCFLAGS = -filetype=obj -relocation-model=pic -mcpu=x86-64 -mattr=-bmi,-bmi2,-tbm,-adx,-avx,-avx2,-fma,-f16c

.PHONY: all clean run run-grub debug debug-grub

all: $(KERNEL_ELF)

ISO_DIR = $(BUILD_DIR)/iso
ISO_BOOT_DIR = $(ISO_DIR)/boot
ISO_GRUB_DIR = $(ISO_BOOT_DIR)/grub
ISO_KERNEL = $(ISO_BOOT_DIR)/$(KERNEL_IMAGE)
ISO_IMAGE = $(BUILD_DIR)/$(ISO_NAME).iso
EFI_APP = $(BUILD_DIR)/BOOTX64.EFI
UEFI_DISK = $(BUILD_DIR)/$(UEFI_DISK_NAME).img
INITRAMFS_IMAGE = $(BUILD_DIR)/initramfs.bin
USER_BUILD_DIR = $(BUILD_DIR)/user
USER_ASM_SRCS = $(wildcard $(USER_DIR)/*.s)
USER_NAMES = $(notdir $(basename $(USER_ASM_SRCS)))
USER_OBJS = $(patsubst %,$(USER_BUILD_DIR)/%.o,$(USER_NAMES))
USER_ELFS = $(patsubst %,$(USER_BUILD_DIR)/%.elf,$(USER_NAMES))
INITRAMFS_STAGE_DIR = $(BUILD_DIR)/initramfs-root
INITRAMFS_STAGE_STAMP = $(BUILD_DIR)/initramfs-root.stamp

$(KERNEL_ELF): $(OBJS) $(LDSCRIPT)
	$(LD) $(LDFLAGS) -T $(LDSCRIPT) -o $@ $(OBJS)

$(ISO_KERNEL): $(KERNEL_ELF)
	@mkdir -p $(ISO_BOOT_DIR)
	cp -f $< $@

$(ISO_GRUB_DIR)/grub.cfg: $(GRUB_CFG)
	@mkdir -p $(ISO_GRUB_DIR)
	sed 's#^\([[:space:]]*multiboot[[:space:]]\+\)/boot/[^[:space:]]*#\1/boot/$(KERNEL_IMAGE)#' $< > $@

$(ISO_IMAGE): $(ISO_KERNEL) $(ISO_GRUB_DIR)/grub.cfg
	grub-mkrescue -o $@ $(ISO_DIR)

$(KERNEL_OBJ): $(KERNEL_LL)
	$(LLC) $(LLCFLAGS) -o $@ $<

$(EFI_LOADER_OBJ): $(EFI_LOADER_SRC)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(EFI_CFLAGS) -c $< -o $@

$(EFI_ENTRY_OBJ): $(EFI_ENTRY_SRC)
	@mkdir -p $(BUILD_DIR)
	as --64 $< -o $@

$(EFI_APP): $(EFI_ENTRY_OBJ) $(EFI_LOADER_OBJ)
	$(LD) $(EFI_LDFLAGS) -o $@ $(EFI_ENTRY_OBJ) $(EFI_LOADER_OBJ)
	$(OBJCOPY) --remove-section .comment --remove-section .eh_frame --remove-section .note.gnu.property $@

$(USER_BUILD_DIR)/%.o: $(USER_DIR)/%.s
	@mkdir -p $(USER_BUILD_DIR)
	$(AS) $(ASFLAGS) $< -o $@

$(USER_BUILD_DIR)/%.elf: $(USER_BUILD_DIR)/%.o $(USER_DIR)/linker.ld
	$(LD) -m elf_x86_64 -nostdlib -T $(USER_DIR)/linker.ld -o $@ $<

$(INITRAMFS_STAGE_STAMP): $(INITRAMFS_SRCS) $(USER_SRCS) $(USER_ELFS)
	@rm -rf $(INITRAMFS_STAGE_DIR)
	@mkdir -p $(INITRAMFS_STAGE_DIR)
	cp -R $(INITRAMFS_DIR)/. $(INITRAMFS_STAGE_DIR)
	@mkdir -p $(INITRAMFS_STAGE_DIR)/bin
	for elf in $(USER_ELFS); do cp -f $$elf $(INITRAMFS_STAGE_DIR)/bin/$$(basename $$elf .elf); done
	@touch $@

$(INITRAMFS_IMAGE): scripts/build-initramfs.py $(INITRAMFS_STAGE_STAMP)
	$(PYTHON) scripts/build-initramfs.py $(INITRAMFS_STAGE_DIR) $@

$(UEFI_DISK): $(EFI_APP) $(KERNEL_ELF) $(INITRAMFS_IMAGE)
	@rm -f $@
	mformat -C -f 2880 -i $@ ::
	mmd -i $@ ::/EFI
	mmd -i $@ ::/EFI/BOOT
	mcopy -i $@ $(EFI_APP) ::/EFI/BOOT/BOOTX64.EFI
	mcopy -i $@ $(KERNEL_ELF) ::/KERNEL.ELF
	mcopy -i $@ $(INITRAMFS_IMAGE) ::/INITRAMFS.BIN

$(KERNEL_LL): $(KERNEL_PY_SRCS)
	@mkdir -p $(BUILD_DIR)
	$(CODON) build --llvm -o $@ $(KERNEL_SRC)

$(BOOT_OBJ): $(BOOT_SRC)
	@mkdir -p $(BUILD_DIR)
	$(AS) $(ASFLAGS) $< -o $@

$(RUNTIME_OBJ): $(RUNTIME_SRC)
	@mkdir -p $(BUILD_DIR)
	$(AS) $(ASFLAGS) $< -o $@

$(INTERRUPTS_OBJ): $(INTERRUPTS_SRC)
	@mkdir -p $(BUILD_DIR)
	$(AS) $(ASFLAGS) $< -o $@

clean:
	@rm -rf $(BUILD_DIR)

run: $(if $(filter x86_64,$(ARCH)),$(UEFI_DISK),all)
	@ISO_NAME=$(ISO_NAME) UEFI_DISK_NAME=$(UEFI_DISK_NAME) KERNEL_TARGET=$(KERNEL_TARGET) ./scripts/run-qemu.sh $(ARCH)

run-grub: $(if $(filter x86_64,$(ARCH)),$(ISO_IMAGE),all)
	@ISO_NAME=$(ISO_NAME) KERNEL_TARGET=$(KERNEL_TARGET) ./scripts/run-qemu.sh $(ARCH)

debug: $(if $(filter x86_64,$(ARCH)),$(UEFI_DISK),all)
	@ISO_NAME=$(ISO_NAME) UEFI_DISK_NAME=$(UEFI_DISK_NAME) KERNEL_TARGET=$(KERNEL_TARGET) ./scripts/debug.sh $(ARCH)

debug-grub: $(if $(filter x86_64,$(ARCH)),$(ISO_IMAGE),all)
	@ISO_NAME=$(ISO_NAME) KERNEL_TARGET=$(KERNEL_TARGET) ./scripts/debug.sh $(ARCH)

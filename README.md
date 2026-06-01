# PCO OS

PCO/OS is a small x86_64 operating-system project built around a Python-first kernel.

The current system boots through UEFI, hands a structured boot block to the kernel, brings up its own memory management, installs exception and timer paths, mounts an initramfs-backed VFS, runs a tiny syscall layer, loads small ELF user programs, and drops into a serial shell.

## Snapshot

- Kernel logic is written mostly in Codon/Python.
- Low-level CPU, boot, interrupt, and runtime edges stay in NASM and C.
- Main boot flow is `OVMF -> BOOTX64.EFI -> KERNEL.ELF -> kernel_main`.
- QEMU + OVMF is the primary bring-up and test environment.
- Serial is the primary debug and verification path.

## Current Capabilities

- UEFI boot through a custom EFI loader
- GRUB fallback boot path
- Structured `BootInfo` handoff into the kernel
- Runtime GDT/TSS setup with dedicated double-fault IST
- IDT installation and exception reporting for `#DE`, `#DF`, `#GP`, and `#PF`
- Physical page allocator built from the EFI memory map
- Kernel-owned page tables with early PMM/VMM self-tests
- Local APIC setup, LAPIC timer probing, live timer IRQ validation, and kernel tick accounting
- Small scheduler with real context switches
- `int 0x80` syscall entry path
- Early descriptor-based file I/O and metadata syscalls
- Tiny hierarchical VFS with read-only initramfs plus writable tmpfs-backed `/tmp`
- ELF-backed ring-3 user-task loading from `/bin/*`
- Tiny serial shell with built-in commands

## Architecture

The project keeps high-level policy in Codon/Python and pushes hardware-facing edges down into low-level code.

- `src/kernel/`
  - boot orchestration
  - boot-info parsing
  - console helpers
  - exception logic
  - PMM and VMM
  - APIC/time helpers
  - scheduler
  - syscalls
  - VFS
  - shell
  - ELF user-image loading
- `src/arch/x86_64/`
  - long-mode entry
  - runtime shims
  - serial I/O
  - context switching
  - descriptor-table setup
  - ISR entry stubs
  - low-level register and port helpers
- `src/boot/uefi/`
  - EFI entry stub
  - UEFI loader that loads `KERNEL.ELF`, captures the EFI memory map, stages `INITRAMFS.BIN`, fills `BootInfo`, exits boot services, and jumps into the kernel
- `src/boot/grub/`
  - fallback GRUB configuration

## Repository Layout

```text
src/
  arch/x86_64/
    boot.s
    interrupts.s
    linker.ld
    runtime.s
  boot/
    grub/
      grub.cfg
    uefi/
      efi_entry.S
      efi_loader.c
  kernel/
    kernel.py
    khal.py
    kboot.py
    kconsole.py
    kelf.py
    kexceptions.py
    kidt.py
    kmemory.py
    kapic.py
    ksched.py
    ksyscall.py
    ktime.py
    kvfs.py
    kshell.py
    ksupport.py
  user/
    *.s
```

## Build

```bash
make
```

Main build artifact:

- `build/kernel-x86_64.elf`

Full boot-path targets also build:

- `build/BOOTX64.EFI`
- `build/initramfs.bin`
- `build/pco_os-x86_64-uefi.img`

GRUB fallback targets build:

- `build/pco_os-x86_64.iso`

## Run

Recommended serial-first smoke test:

```bash
HEADLESS=1 make run
```

Visible QEMU window:

```bash
HEADLESS=0 make run
```

GRUB fallback path:

```bash
make run-grub
```

## Debug

UEFI path:

```bash
make debug
```

GRUB fallback path:

```bash
make debug-grub
```

Clean artifacts:

```bash
make clean
```

## Build Flow

1. `src/kernel/*.py` is compiled with Codon to LLVM IR.
2. `build/kernel.ll` is lowered with `llc` to `build/kernel.o`.
3. `boot.s`, `runtime.s`, and `interrupts.s` are assembled with NASM.
4. Everything is linked with `src/arch/x86_64/linker.ld` into `build/kernel-x86_64.elf`.
5. The EFI loader is built from `src/boot/uefi/efi_entry.S` and `src/boot/uefi/efi_loader.c` into `build/BOOTX64.EFI`.
6. Tiny user ELF binaries from `src/user/` are staged into the initramfs under `/bin/`.
7. `initramfs/` plus staged user binaries are packed into `build/initramfs.bin`.
8. `BOOTX64.EFI`, `KERNEL.ELF`, and `INITRAMFS.BIN` are staged into a FAT disk image and booted with QEMU + OVMF.

## Healthy Boot Output

Current healthy serial output should include lines like:

- `Hello from Codon over serial!`
- `boot.method=uefi-loader`
- `pmm self-test ok`
- `vmm self-test ok`
- `vfs self-test ok`
- `lapic timer probe ok`
- `lapic timer irq ok`
- `timekeeping self-test ok`
- `scheduler self-test ok`
- `syscall self-test ok`
- `shell self-test ok`
- `shell ready`
- `pco> `

Later parts of the log should also show user-task execution, for example:

- `task1 waitpid=2 status=42`
- `task1 rwtest waitpid=2 status=42`
- `task1 argv waitpid=2 status=33`
- `task1 chain waitpid=2 status=33`
- `task1 heap status=88`
- `task1 adopted status=7`
- `task1 preempt fast status=7`
- `task1 preempt slow status=55`

## Shell

The current serial shell is intentionally small and bring-up oriented. Built-ins include:

- `help`
- `pwd`
- `ppid`
- `cd`
- `clear`
- `ls`
- `cat`
- `stat`
- `write`
- `ticks`
- `spawn`
- `run`

## Design Notes

- Serial is the most reliable early-boot output path.
- VGA exists as a secondary path, but it is not the source of truth during bring-up.
- The kernel now owns its own `cr3` and no longer relies on firmware page tables after early bootstrap.
- The current VM layout is still identity-first. Higher-half cleanup and richer VM policy are future work.
- The current process/syscall layer is intentionally small and POSIX-ish, not full POSIX.
- Preemption is working for user-mode tasks via the LAPIC timer path; broader kernel-mode preemption is still not a goal yet.

## Practical Developer Notes

- If the screen looks blank, check serial output first.
- If a change affects boot, memory, or interrupts, prefer `HEADLESS=1 make run` before anything else.
- The UEFI path is the primary path. GRUB remains useful as a fallback and debug aid.
- Deeper project notes live in:
  - `Learning.md`
  - `CurrentContext.md`

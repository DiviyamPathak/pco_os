# PCO OS

Small x86_64 OS experiment with:
- a Python-first kernel written in Codon
- a UEFI loader in C/assembly
- low-level arch code in NASM
- QEMU + OVMF as the main bring-up environment

## Layout

```text
src/
  arch/x86_64/
    boot.s
    interrupts.s
    linker.ld
    runtime.s
  boot/
    grub/grub.cfg
    uefi/
      efi_entry.S
      efi_loader.c
  kernel/
    kernel.py
```

## Build

```bash
make
```

This builds the kernel ELF:
- `build/kernel-x86_64.elf`

Targets that need the full boot path build extra artifacts automatically:
- `make run` or `make debug` also build `build/BOOTX64.EFI`
- `make run` or `make debug` also build `build/initramfs.bin`
- `make run` or `make debug` also build `build/pco_os-x86_64-uefi.img`
- `make run-grub` or `make debug-grub` build `build/pco_os-x86_64.iso`

## Run

Default run path:

```bash
make run
```

That boots the UEFI disk image with QEMU + OVMF and is headless by default because `scripts/run-qemu.sh` uses `HEADLESS=1` unless you override it.

Recommended serial smoke test:

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

```bash
make debug
```

This starts QEMU paused with `-s -S` and attaches GDB against `build/kernel-x86_64.elf`.

GRUB fallback debug path:

```bash
make debug-grub
```

Clean build artifacts:

```bash
make clean
```

## What The Makefile Does

- `make` compiles `src/kernel/kernel.py` to `build/kernel.ll`, lowers it with `llc`, assembles `boot.s`, `runtime.s`, and `interrupts.s`, then links `build/kernel-x86_64.elf`.
- `make run` builds the EFI loader from `src/boot/uefi/efi_entry.S` and `src/boot/uefi/efi_loader.c`, stages `BOOTX64.EFI` plus `KERNEL.ELF` into a FAT disk image, then boots it with QEMU + OVMF.
- `make run` also packs `initramfs/` into `build/initramfs.bin`, stages it as `INITRAMFS.BIN`, and hands it to the kernel through the UEFI boot-info block.
- `make run` also builds tiny user ELF binaries from `src/user/`, stages them into the initramfs under `/bin/`, packs the result into `build/initramfs.bin`, and hands it to the kernel through the UEFI boot-info block.
- `make run-grub` stages the kernel ELF into a GRUB ISO and boots the fallback path.
- `make debug` and `make debug-grub` follow the same image path, then start QEMU in GDB wait mode.

## Quick Test Loop

```bash
make
HEADLESS=1 make run
```

Current healthy serial output should include lines like:
- `Hello from Codon over serial!`
- `boot.method=uefi-loader`
- `pmm self-test ok`
- `vmm self-test ok`
- `lapic timer probe ok`
- `lapic timer irq ok`
- `timekeeping self-test ok`
- `vfs self-test ok`
- `sys.fstat.size=22`
- `sys.readdir.sample=bin`
- `sys.read.tmp.sample=tmpfs-ok`
- `sys.read.stdin=0`
- `shell self-test ok`
- `shell ready`
- `pco> `
- `scheduler self-test ok`
- `sys.close.bad=-1`
- `syscall self-test ok`
- `task1 spawned pid=2`
- `task1 waitpid=2 status=42`
- `user syscall exit`
- `task1 rwtest waitpid=2 status=42`
- `task1 chain waitpid=2 status=33`
- `task1 heap status=88`
- `task1 adopted status=7`
- `task1 preempt fast status=7`
- `task1 preempt slow status=55`
- `run pid=2`
- `run status=33`

## Notes

- The primary x86_64 boot path is UEFI: `OVMF -> BOOTX64.EFI -> KERNEL.ELF -> kernel_main`.
- Serial is the most reliable early-boot output path.
- Bootstrap tasks now run with saved task contexts, and the kernel can dynamically spawn, reap, and respawn tiny ring-3 user programs on fresh per-task CR3 roots with a shared private user layout through a user-capable `int 0x80` path.
- The syscall ABI now has early file-descriptor and filesystem support: tasks start with `stdin/stdout/stderr`, `open/read/write/close` are wired through descriptor objects, and the current syscall self-test now also proves `fstat`-style metadata, `getppid`, plus root-directory `readdir` on the initramfs-backed VFS.
- `stdin` is now a nonblocking serial-backed descriptor, so `read(fd=0, ...)` is live for interactive bring-up without stalling unattended boots.
- A tiny serial shell now runs in task 1 after the scheduler/process self-tests, with line buffering, backspace handling, a prompt, and built-in commands for `help`, `pwd`, `ppid`, `cd`, `clear`, `ls`, `cat`, `stat`, `write`, `ticks`, `spawn`, and `run`.
- The current storage path is a small hierarchical VFS made from a read-only initramfs root plus a writable tmpfs-backed `/tmp`, with a real root directory, nested directories like `/bin` and `/docs`, read-only regular files, mutable tmpfs files, and tiny ELF user binaries.
- The current exec path is ELF-backed instead of built-in-program-backed: the kernel opens the file from the VFS, validates a tiny ELF64 subset, maps multiple `PT_LOAD` segments with writable data/BSS handling into a ring-3 task, and can either spawn a new task or replace the current user image through the same loader path.
- Parent-child bookkeeping is now explicit enough for `waitpid` ownership, `waitpid(-1)` adoption/reap behavior, and `getppid`, and both spawned-user and direct user-side `execve(argv, envp)` proof paths now carry `argv/envp` into userspace through the initial task stack and user-entry registers.
- User tasks now have an explicit heap region inside their private user mapping, and the syscall layer exposes a small `brk`-style interface that `/bin/heap` proves during boot.
- Timer-driven preemption now includes direct LAPIC IRQ-side rescheduling for user-mode tasks, so a pure userspace busy loop can be preempted without waiting for a syscall or trap return; broader kernel-mode preemption is still not a target yet.
- Current project notes and handoff state live in:
  - `Learning.md`
  - `CurrentContext.md`

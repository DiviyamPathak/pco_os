MBALIGN  equ  1 << 0
MEMINFO  equ  1 << 1
FLAGS    equ  MBALIGN | MEMINFO
MAGIC    equ  0x1BADB002
CHECKSUM equ -(MAGIC + FLAGS)

section .multiboot
align 4
    dd MAGIC
    dd FLAGS
    dd CHECKSUM

section .bss
alignb 4
multiboot_magic:
    resd 1
multiboot_info_ptr:
    resd 1
alignb 4096
p4_table:
    resb 4096
p3_table:
    resb 4096
p2_table:
    resb 4096
stack_bottom:
    resb 16384
stack_top:
alignb 16
boot_info:
    resq 23

section .rodata
gdt64:
    dq 0
.code: equ $ - gdt64
    dq (1<<43) | (1<<44) | (1<<47) | (1<<53)
.data: equ $ - gdt64
    dq (1<<41) | (1<<44) | (1<<47)
.pointer:
    dw $ - gdt64 - 1
    dq gdt64

section .bootmeta
align 8
global kernel_bootmeta
global kernel_entry64
kernel_bootmeta:
    dq 0x50434F4D45544131
    dq 1
    dq kernel_entry64

section .text
bits 32
global _start
extern __kernel_start
extern __kernel_end
extern kernel_main

_start:
    mov [multiboot_magic], eax
    mov [multiboot_info_ptr], ebx
    mov esp, stack_top

    mov eax, p3_table
    or eax, 0b11
    mov [p4_table], eax

    mov eax, p2_table
    or eax, 0b11
    mov [p3_table], eax

    mov ecx, 0
.map_p2_table:
    mov eax, 0x200000
    mul ecx
    or eax, 0b10000011
    mov [p2_table + ecx * 8], eax
    inc ecx
    cmp ecx, 512
    jne .map_p2_table

    mov eax, cr4
    or eax, 1 << 5
    mov cr4, eax

    mov eax, p4_table
    mov cr3, eax

    mov ecx, 0xC0000080
    rdmsr
    or eax, 1 << 8
    wrmsr

    mov eax, cr0
    or eax, 1 << 31
    mov cr0, eax

    lgdt [gdt64.pointer]
    jmp gdt64.code:long_mode_start

bits 64
long_mode_start:
    mov ax, gdt64.data
    mov ss, ax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    mov rax, 0x50434F424F4F5431
    mov [boot_info + 0 * 8], rax
    mov qword [boot_info + 1 * 8], 1
    mov qword [boot_info + 2 * 8], 1
    mov qword [boot_info + 3 * 8], 0
    mov qword [boot_info + 4 * 8], 0
    mov qword [boot_info + 5 * 8], 0
    mov qword [boot_info + 6 * 8], 0
    mov qword [boot_info + 7 * 8], 0
    mov qword [boot_info + 8 * 8], 0
    mov qword [boot_info + 9 * 8], 0
    mov qword [boot_info + 10 * 8], 0
    mov qword [boot_info + 11 * 8], 0
    mov qword [boot_info + 12 * 8], 0
    mov rax, __kernel_start
    mov [boot_info + 13 * 8], rax
    mov rax, __kernel_end
    mov [boot_info + 14 * 8], rax
    mov rax, __kernel_start
    mov [boot_info + 15 * 8], rax
    mov rax, __kernel_end
    mov [boot_info + 16 * 8], rax
    mov qword [boot_info + 17 * 8], 0
    mov qword [boot_info + 18 * 8], 1
    mov eax, [multiboot_info_ptr]
    mov [boot_info + 19 * 8], rax
    mov eax, [multiboot_magic]
    mov [boot_info + 20 * 8], rax
    mov qword [boot_info + 21 * 8], 0
    mov qword [boot_info + 22 * 8], 0

    lea rdi, [rel boot_info]
    call kernel_entry64

kernel_entry64:
    call kernel_main

    cli
.hang:
    hlt
    jmp .hang

section .note.GNU-stack noalloc noexec nowrite progbits

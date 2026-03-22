section .text
bits 64

global load_idt
global load_idt_local
global arch_init
global read_cr2
global read_apic_id
global get_idt_base
global get_idtr_base
global set_idt_gate_asm
global set_idtr_asm
global frame_qword_asm
global store_qword_asm
global get_isr0_addr
global get_isr8_addr
global get_isr13_addr
global get_isr14_addr
global isr0
global isr8
global isr13
global isr14
global trigger_interrupt0
global trigger_divide_error
global trigger_general_protection
global trigger_page_fault

extern isr_dispatch

%macro PUSH_REGS 0
    push r15
    push r14
    push r13
    push r12
    push r11
    push r10
    push r9
    push r8
    push rbp
    push rdi
    push rsi
    push rdx
    push rcx
    push rbx
    push rax
%endmacro

%macro POP_REGS 0
    pop rax
    pop rbx
    pop rcx
    pop rdx
    pop rsi
    pop rdi
    pop rbp
    pop r8
    pop r9
    pop r10
    pop r11
    pop r12
    pop r13
    pop r14
    pop r15
%endmacro

load_idt:
    lidt [rdi]
    ret

load_idt_local:
    lea rax, [rel idtr]
    lidt [rax]
    ret

arch_init:
    lea rax, [rel tss64]
    mov rdx, rax
    lea rcx, [rel gdt64_tss_desc]
    mov word [rcx], 103
    mov word [rcx + 2], dx
    shr rdx, 16
    mov byte [rcx + 4], dl
    mov byte [rcx + 5], 0x89
    mov byte [rcx + 6], 0
    shr rdx, 8
    mov byte [rcx + 7], dl
    shr rdx, 8
    mov dword [rcx + 8], edx
    mov dword [rcx + 12], 0

    lea rax, [rel gdt64_runtime_pointer]
    lgdt [rax]

    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    lea rax, [rel kernel_rsp0_top]
    mov [rel tss64 + 4], rax
    lea rax, [rel df_ist_top]
    mov [rel tss64 + 36], rax
    mov word [rel tss64 + 102], 104

    mov ax, 0x18
    ltr ax
    ret

read_cr2:
    mov rax, cr2
    ret

read_apic_id:
    push rbx
    mov eax, 1
    cpuid
    shr ebx, 24
    mov eax, ebx
    pop rbx
    ret

get_idt_base:
    lea rax, [rel idt_table]
    ret

get_idtr_base:
    lea rax, [rel idtr]
    ret

set_idt_gate_asm:
    lea rax, [rel idt_table]
    mov rcx, rdi
    shl rcx, 4
    add rax, rcx

    mov word [rax], si
    mov word [rax + 2], 0x08
    mov byte [rax + 4], dl
    mov byte [rax + 5], 0x8E
    shr rsi, 16
    mov word [rax + 6], si
    shr rsi, 16
    mov dword [rax + 8], esi
    mov dword [rax + 12], 0
    ret

set_idtr_asm:
    lea rax, [rel idtr]
    mov word [rax], di
    mov qword [rax + 2], rsi
    ret

frame_qword_asm:
    mov rax, [rdi + rsi * 8]
    ret

store_qword_asm:
    mov [rdi + rsi * 8], rdx
    ret

get_isr0_addr:
    mov rax, isr0
    ret

get_isr8_addr:
    mov rax, isr8
    ret

get_isr13_addr:
    mov rax, isr13
    ret

get_isr14_addr:
    mov rax, isr14
    ret

isr0:
    push 0
    push 0
    jmp isr_common

isr8:
    push 8
    jmp isr_common

isr13:
    push 13
    jmp isr_common

isr14:
    push 14
    jmp isr_common

isr_common:
    PUSH_REGS
    sub rsp, 8
    lea rdi, [rsp + 8]
    mov rsi, [rsp + 8 + 15 * 8]
    mov rdx, [rsp + 8 + 16 * 8]
    call isr_dispatch
    add rsp, 8
    POP_REGS
    add rsp, 16
    iretq

trigger_interrupt0:
    int 0
    ret

trigger_divide_error:
    xor rdx, rdx
    mov rax, 1
    xor rcx, rcx
    div rcx
    ret

trigger_general_protection:
    xor eax, eax
    mov ss, ax
    ret

trigger_page_fault:
    mov rax, [0x50000000]
    ret

section .data
align 16
gdt64_runtime:
    dq 0
.code: equ $ - gdt64_runtime
    dq (1<<43) | (1<<44) | (1<<47) | (1<<53)
.data: equ $ - gdt64_runtime
    dq (1<<41) | (1<<44) | (1<<47)
.tss: equ $ - gdt64_runtime
gdt64_tss_desc:
    dq 0
    dq 0
gdt64_runtime_pointer:
    dw $ - gdt64_runtime - 1
    dq gdt64_runtime

section .bss
alignb 16
idt_table:
    resb 256 * 16
idtr:
    resb 10
tss64:
    resb 104
alignb 16
kernel_rsp0_bottom:
    resb 4096
kernel_rsp0_top:
alignb 16
df_ist_bottom:
    resb 4096
df_ist_top:

section .note.GNU-stack noalloc noexec nowrite progbits

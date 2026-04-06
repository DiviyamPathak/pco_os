section .text
bits 64

global load_idt
global load_idt_local
global arch_init
global read_cr2
global read_cr3
global load_cr3
global read_apic_id
global cpu_has_apic
global read_msr_asm
global write_msr_asm
global load_dword_asm
global store_dword_asm
global outb_asm
global enable_interrupts
global disable_interrupts
global halt_cpu
global wait_for_interrupt
global set_lapic_eoi_reg_asm
global read_timer_irq_count_asm
global clear_timer_irq_count_asm
global get_idt_base
global get_idtr_base
global set_idt_gate_asm
global set_idt_gate_user_asm
global set_idtr_asm
global set_tss_rsp0_asm
global frame_qword_asm
global store_qword_asm
global get_isr0_addr
global get_isr8_addr
global get_isr13_addr
global get_isr14_addr
global get_isr32_addr
global get_isr128_addr
global isr0
global isr8
global isr13
global isr14
global isr32
global isr128
global trigger_interrupt0
global trigger_divide_error
global trigger_general_protection
global trigger_page_fault

extern isr_dispatch
extern syscall_entry

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

    lea rax, [rel .runtime_cs_loaded]
    push qword 0x08
    push rax
    retfq

.runtime_cs_loaded:

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
    lea rax, [rel irq_ist_top]
    mov [rel tss64 + 44], rax
    mov word [rel tss64 + 102], 104

    mov ax, 0x28
    ltr ax
    ret

read_cr2:
    mov rax, cr2
    ret

read_cr3:
    mov rax, cr3
    ret

load_cr3:
    mov rax, rdi
    mov cr3, rax
    ret

read_apic_id:
    push rbx
    mov eax, 1
    cpuid
    shr ebx, 24
    mov eax, ebx
    pop rbx
    ret

cpu_has_apic:
    push rbx
    mov eax, 1
    cpuid
    shr edx, 9
    and edx, 1
    mov eax, edx
    pop rbx
    ret

read_msr_asm:
    mov ecx, edi
    rdmsr
    shl rdx, 32
    or rax, rdx
    ret

write_msr_asm:
    mov ecx, edi
    mov rax, rsi
    mov rdx, rsi
    shr rdx, 32
    wrmsr
    ret

load_dword_asm:
    mov eax, [rdi]
    ret

store_dword_asm:
    mov [rdi], esi
    ret

outb_asm:
    mov dx, di
    mov al, sil
    out dx, al
    ret

enable_interrupts:
    sti
    ret

disable_interrupts:
    cli
    ret

halt_cpu:
    hlt
    ret

wait_for_interrupt:
    sti
    hlt
    cli
    ret

set_lapic_eoi_reg_asm:
    mov [rel lapic_eoi_reg], rdi
    ret

read_timer_irq_count_asm:
    mov rax, [rel timer_irq_count]
    ret

clear_timer_irq_count_asm:
    mov qword [rel timer_irq_count], 0
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

set_idt_gate_user_asm:
    lea rax, [rel idt_table]
    mov rcx, rdi
    shl rcx, 4
    add rax, rcx

    mov word [rax], si
    mov word [rax + 2], 0x08
    mov byte [rax + 4], dl
    mov byte [rax + 5], 0xEE
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

set_tss_rsp0_asm:
    mov [rel tss64 + 4], rdi
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

get_isr32_addr:
    mov rax, isr32
    ret

get_isr128_addr:
    mov rax, isr128
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

isr32:
    PUSH_REGS
    mov rax, [rel lapic_eoi_reg]
    test rax, rax
    jz .skip_eoi
    mov dword [rax], 0
.skip_eoi:
    inc qword [rel timer_irq_count]
    POP_REGS
    iretq

isr128:
    PUSH_REGS
    mov rdi, [rsp + 0]
    mov rsi, [rsp + 40]
    mov rdx, [rsp + 32]
    mov rcx, [rsp + 24]
    mov r8, [rsp + 72]
    mov r9, [rsp + 56]
    call syscall_entry
    mov [rsp + 0], rax
    POP_REGS
    iretq

isr_common:
    PUSH_REGS
    sub rsp, 136
    lea rdi, [rsp + 136]
    mov rsi, [rsp + 136 + 15 * 8]
    mov rdx, [rsp + 136 + 16 * 8]
    call isr_dispatch
    add rsp, 136
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
.user_code: equ $ - gdt64_runtime
    dq (1<<43) | (1<<44) | (1<<47) | (1<<53) | (3<<45)
.user_data: equ $ - gdt64_runtime
    dq (1<<41) | (1<<44) | (1<<47) | (3<<45)
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
alignb 8
lapic_eoi_reg:
    resq 1
timer_irq_count:
    resq 1
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
alignb 16
irq_ist_bottom:
    resb 4096
irq_ist_top:

section .note.GNU-stack noalloc noexec nowrite progbits

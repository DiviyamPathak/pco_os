section .text
global memcpy
global strlen
global seq_alloc
global seq_alloc_atomic
global seq_alloc_atomic_uncollectable
global seq_init
global seq_personality
global seq_stderr
global seq_stdin
global seq_stdout
global seq_terminate
global serial_init
global serial_rx_ready
global serial_read_byte
global serial_write_byte
global serial_write_u64
global serial_write_hex
global set_active_scheduler_asm
global get_active_scheduler_asm
global context_switch_asm
global restore_task_context_asm
global get_task_trampoline_addr_asm
global get_user_task_trampoline_addr_asm
global get_user_demo_entry_addr_asm
global get_user_hello_entry_addr_asm
global enter_user_mode_asm
global invoke_syscall_asm

extern task_bootstrap
extern task_returned

section .bss
align 16
heap_space:
    resb 262144
heap_end:
heap_ptr:
    resq 1
u64_buffer:
    resb 32
active_scheduler_ptr:
    resq 1

section .text

COM1 equ 0x3F8

memcpy:
    mov rax, rdi
    mov rcx, rdx
    rep movsb
    ret

strlen:
    xor rax, rax
    mov rdi, rdi
.loop:
    cmp byte [rdi + rax], 0
    je .done
    inc rax
    jmp .loop
.done:
    ret

seq_alloc:
    jmp seq_alloc_atomic

seq_alloc_atomic:
    mov rax, [rel heap_ptr]
    test rax, rax
    jnz .have_heap
    lea rax, [rel heap_space]
.have_heap:
    mov rcx, rdi
    add rcx, 15
    and rcx, -16
    lea rdx, [rax + rcx]
    lea r8, [rel heap_end]
    cmp rdx, r8
    ja .oom
    mov [rel heap_ptr], rdx
    ret
.oom:
    xor rax, rax
    ret

seq_alloc_atomic_uncollectable:
    jmp seq_alloc_atomic

seq_init:
    lea rax, [rel heap_space]
    mov [rel heap_ptr], rax
    ret

seq_personality:
    ret
    
seq_stderr:
    xor rax, rax
    ret

seq_stdin:
    xor rax, rax
    ret

seq_stdout:
    xor rax, rax
    ret

seq_terminate:
.loop:
    cli
    hlt
    jmp .loop

serial_init:
    mov dx, COM1 + 1
    xor al, al
    out dx, al

    mov dx, COM1 + 3
    mov al, 0x80
    out dx, al

    mov dx, COM1 + 0
    mov al, 0x01
    out dx, al

    mov dx, COM1 + 1
    xor al, al
    out dx, al

    mov dx, COM1 + 3
    mov al, 0x03
    out dx, al

    mov dx, COM1 + 2
    mov al, 0xC7
    out dx, al

    mov dx, COM1 + 4
    mov al, 0x0B
    out dx, al
    ret

serial_write_byte:
    mov al, dil
.wait:
    mov dx, COM1 + 5
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, COM1
    mov al, dil
    out dx, al
    ret

serial_rx_ready:
    mov dx, COM1 + 5
    in al, dx
    and eax, 1
    ret

serial_read_byte:
    mov dx, COM1
    in al, dx
    movzx eax, al
    ret

serial_write_u64:
    mov rax, rdi
    test rax, rax
    jnz .convert
    mov dil, '0'
    call serial_write_byte
    ret

.convert:
    lea r8, [rel u64_buffer + 31]
    mov byte [r8], 0
    mov rcx, 10

.loop:
    xor rdx, rdx
    div rcx
    add dl, '0'
    dec r8
    mov [r8], dl
    test rax, rax
    jnz .loop

.emit:
    mov dil, [r8]
    test dil, dil
    jz .done
    call serial_write_byte
    inc r8
    jmp .emit

.done:
    ret

serial_write_hex:
    mov r8, rdi
    mov dil, '0'
    call serial_write_byte
    mov dil, 'x'
    call serial_write_byte

    mov rcx, 16
.hex_loop:
    mov rax, r8
    shr rax, 60
    cmp al, 9
    jbe .digit
    add al, 'A' - 10
    jmp .emit_hex
.digit:
    add al, '0'
.emit_hex:
    mov dil, al
    call serial_write_byte
    shl r8, 4
    dec rcx
    jnz .hex_loop
    ret

set_active_scheduler_asm:
    mov [rel active_scheduler_ptr], rdi
    ret

get_active_scheduler_asm:
    mov rax, [rel active_scheduler_ptr]
    ret

context_switch_asm:
    mov [rdi + 0], rsp
    mov [rdi + 8], rbx
    mov [rdi + 16], rbp
    mov [rdi + 24], r12
    mov [rdi + 32], r13
    mov [rdi + 40], r14
    mov [rdi + 48], r15

    mov rsp, [rsi + 0]
    mov rbx, [rsi + 8]
    mov rbp, [rsi + 16]
    mov r12, [rsi + 24]
    mov r13, [rsi + 32]
    mov r14, [rsi + 40]
    mov r15, [rsi + 48]
    ret

restore_task_context_asm:
    mov rsp, [rdi + 0]
    mov rbx, [rdi + 8]
    mov rbp, [rdi + 16]
    mov r12, [rdi + 24]
    mov r13, [rdi + 32]
    mov r14, [rdi + 40]
    mov r15, [rdi + 48]
    ret

get_task_trampoline_addr_asm:
    mov rax, task_trampoline_asm
    ret

get_user_task_trampoline_addr_asm:
    mov rax, user_task_trampoline_asm
    ret

get_user_demo_entry_addr_asm:
    mov rax, user_demo_entry_asm
    ret

get_user_hello_entry_addr_asm:
    mov rax, user_hello_entry_asm
    ret

enter_user_mode_asm:
    mov ax, 0x23
    mov ds, ax
    mov es, ax
    push qword 0x23
    push rsi
    pushfq
    or qword [rsp], 0x200
    push qword 0x1B
    push rdi
    iretq

invoke_syscall_asm:
    mov rax, rdi
    mov rdi, rsi
    mov rsi, rdx
    mov rdx, rcx
    mov r10, r8
    mov r8, r9
    int 0x80
    ret

task_trampoline_asm:
    mov rdi, r12
    call task_bootstrap
    xor edi, edi
    call task_returned
.halt:
    cli
    hlt
    jmp .halt

user_task_trampoline_asm:
    mov rdi, r12
    mov rsi, r13
    call enter_user_mode_asm
    xor edi, edi
    call task_returned
.user_halt:
    cli
    hlt
    jmp .user_halt

align 4096
user_demo_entry_asm:
    mov eax, 2
    int 0x80

    mov ecx, 3
.yield_loop:
    mov eax, 4
    int 0x80
    dec ecx
    jnz .yield_loop

    lea rdi, [r14 + 0]
    mov esi, 10
    xor edx, edx
    mov eax, 9
    int 0x80

    mov ebx, eax
    mov edi, eax
    lea rsi, [r14 + 128]
    mov edx, 64
    mov eax, 10
    int 0x80

    mov edx, eax
    mov edi, 1
    lea rsi, [r14 + 128]
    mov eax, 1
    int 0x80

    mov edi, ebx
    mov eax, 8
    int 0x80

    mov edi, 42
    mov eax, 5
    int 0x80
.spin:
    jmp .spin

align 4096
user_hello_entry_asm:
    mov edi, 1
    lea rsi, [rel user_hello_message]
    mov edx, user_hello_message_end - user_hello_message
    mov eax, 1
    int 0x80

    mov edi, 7
    mov eax, 5
    int 0x80
.spin_hello:
    jmp .spin_hello

user_hello_message:
    db "Hello from user program!", 10
user_hello_message_end:

section .note.GNU-stack noalloc noexec nowrite progbits

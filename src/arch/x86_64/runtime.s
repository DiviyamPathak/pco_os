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
global serial_write_byte
global serial_write_u64
global serial_write_hex

section .bss
align 16
heap_space:
    resb 65536
heap_end:
heap_ptr:
    resq 1
u64_buffer:
    resb 32

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

section .note.GNU-stack noalloc noexec nowrite progbits

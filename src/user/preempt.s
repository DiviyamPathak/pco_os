default rel
section .text
global _start

_start:
    mov eax, 3
    int 0x80
    mov r12d, eax
    add r12d, 4

.wait_ticks:
    mov eax, 3
    int 0x80
    cmp eax, r12d
    jl .wait_ticks

    mov edi, 1
    lea rsi, [rel done_message]
    mov edx, done_message_len
    mov eax, 1
    int 0x80

    mov edi, 55
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
done_message:
    db "preempt child done", 10
done_message_len equ $ - done_message

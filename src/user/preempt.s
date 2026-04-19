default rel
section .text
global _start

_start:
    mov ecx, 200000000

.spin:
    dec ecx
    jnz .spin

    mov edi, 1
    lea rsi, [rel done_message]
    mov edx, done_message_len
    mov eax, 1
    int 0x80

    mov edi, 55
    mov eax, 5
    int 0x80

.halt:
    jmp .halt

section .rodata
done_message:
    db "preempt child done", 10
done_message_len equ $ - done_message

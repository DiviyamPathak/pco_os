default rel
section .text
global _start

_start:
    mov edi, 1
    lea rsi, [rel hello_message]
    mov edx, hello_message_len
    mov eax, 1
    int 0x80

    mov edi, 7
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
hello_message:
    db "Hello from user program!", 10
hello_message_len equ $ - hello_message

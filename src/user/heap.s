default rel
section .text
global _start

_start:
    xor edi, edi
    mov eax, 16
    int 0x80
    mov rbx, rax

    lea rdi, [rbx + 8]
    mov eax, 16
    int 0x80

    mov byte [rbx + 0], 'h'
    mov byte [rbx + 1], 'e'
    mov byte [rbx + 2], 'a'
    mov byte [rbx + 3], 'p'
    mov byte [rbx + 4], '-'
    mov byte [rbx + 5], 'o'
    mov byte [rbx + 6], 'k'
    mov byte [rbx + 7], 10

    mov edi, 1
    mov rsi, rbx
    mov edx, 8
    mov eax, 1
    int 0x80

    mov edi, 88
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

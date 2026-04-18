default rel
section .text
global _start

_start:
    mov rax, [rel counter]
    add rax, 1
    mov [rel counter], rax

    mov byte [rel scratch + 0], 'R'
    mov byte [rel scratch + 1], 'W'
    mov byte [rel scratch + 2], 10

    cmp qword [rel counter], 42
    jne .fail
    cmp byte [rel scratch + 0], 'R'
    jne .fail
    cmp byte [rel scratch + 1], 'W'
    jne .fail

    mov edi, 1
    lea rsi, [rel scratch]
    mov edx, 3
    mov eax, 1
    int 0x80

    mov edi, 42
    mov eax, 5
    int 0x80

.fail:
    mov edi, 1
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .data
counter:
    dq 41

section .bss
scratch:
    resb 16

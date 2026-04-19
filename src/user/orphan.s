default rel
section .text
global _start

_start:
    lea rdi, [rel hello_path]
    mov esi, hello_path_len
    xor edx, edx
    xor r10d, r10d
    mov eax, 13
    int 0x80

    mov edi, 21
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
hello_path:
    db "/bin/hello"
hello_path_len equ $ - hello_path

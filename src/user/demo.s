default rel
section .text
global _start

_start:
    sub rsp, 128

    lea rdi, [rel hello_path]
    mov esi, hello_path_len
    xor edx, edx
    mov eax, 9
    int 0x80

    mov ebx, eax
    test eax, eax
    js .exit_fail

    mov edi, eax
    mov rsi, rsp
    mov edx, 64
    mov eax, 10
    int 0x80

    mov edx, eax
    test eax, eax
    jle .close_and_exit

    mov edi, 1
    mov rsi, rsp
    mov eax, 1
    int 0x80

.close_and_exit:
    mov edi, ebx
    mov eax, 8
    int 0x80

    mov edi, 42
    mov eax, 5
    int 0x80

.exit_fail:
    mov edi, 1
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
hello_path:
    db "/hello.txt"
hello_path_len equ $ - hello_path

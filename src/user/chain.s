default rel
section .text
global _start

_start:
    mov edi, 1
    lea rsi, [rel chain_message]
    mov edx, chain_message_len
    mov eax, 1
    int 0x80

    lea rdi, [rel argv_path]
    mov esi, argv_path_len
    xor edx, edx
    xor r10d, r10d
    mov eax, 14
    int 0x80

    mov edi, 1
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
chain_message:
    db "Chaining into /bin/hello", 10
chain_message_len equ $ - chain_message

argv_path:
    db "/bin/hello"
argv_path_len equ $ - argv_path

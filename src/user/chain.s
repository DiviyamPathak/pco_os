default rel
section .text
global _start

_start:
    mov edi, 1
    lea rsi, [rel chain_message]
    mov edx, chain_message_len
    mov eax, 1
    int 0x80

    sub rsp, 40
    lea r11, [rel arg0]
    lea r12, [rel arg1]
    lea r13, [rel env0]
    mov [rsp + 0], r11
    mov [rsp + 8], r12
    mov qword [rsp + 16], 0
    mov [rsp + 24], r13
    mov qword [rsp + 32], 0

    lea rdi, [rel argv_path]
    mov esi, argv_path_len
    lea rdx, [rsp + 0]
    lea r10, [rsp + 24]
    mov eax, 14
    int 0x80

    mov edi, 1
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

section .rodata
chain_message:
    db "Chaining into /bin/argv", 10
chain_message_len equ $ - chain_message

argv_path:
    db "/bin/argv"
argv_path_len equ $ - argv_path

arg0:
    db "/bin/argv", 0
arg1:
    db "exec-argv", 0
env0:
    db "MODE=execve", 0

default rel
section .text
global _start

_start:
    cmp rdi, 2
    jb .bad

    mov rbx, rsi
    mov r12, rdx

    mov rsi, [rbx + 8]
    call print_cstring
    call print_newline

    mov rsi, [r12 + 0]
    test rsi, rsi
    jz .done
    call print_cstring
    call print_newline

.done:
    mov edi, 33
    mov eax, 5
    int 0x80

.bad:
    mov edi, 1
    mov eax, 5
    int 0x80

.spin:
    jmp .spin

print_cstring:
    xor edx, edx
.len:
    cmp byte [rsi + rdx], 0
    je .emit
    inc rdx
    jmp .len
.emit:
    mov edi, 1
    mov eax, 1
    int 0x80
    ret

print_newline:
    mov edi, 1
    lea rsi, [rel newline]
    mov edx, 1
    mov eax, 1
    int 0x80
    ret

section .rodata
newline:
    db 10

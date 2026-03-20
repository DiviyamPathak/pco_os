.intel_syntax noprefix
.text
.globl efi_entry
.type efi_entry, @function
.extern efi_main_body

efi_entry:
    push rbp
    mov rbp, rsp
    push rdi
    push rsi
    sub rsp, 32
    mov rdi, rcx
    mov rsi, rdx
    call efi_main_body
    add rsp, 32
    pop rsi
    pop rdi
    leave
    ret

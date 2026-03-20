ENTRY(_start)

PHDRS
{
    text PT_LOAD FLAGS(5);
    data PT_LOAD FLAGS(6);
}

SECTIONS
{
    . = 1M;
    __kernel_start = .;

    .multiboot :
    {
        KEEP(*(.multiboot))
    } :text

    .text :
    {
        *(.text*)
    } :text

    .bootmeta :
    {
        KEEP(*(.bootmeta))
    } :text

    .rodata :
    {
        *(.rodata*)
        *(.gcc_except_table*)
    } :text

    .data :
    {
        *(.data*)
    } :data

    .bss :
    {
        *(.bss*)
        *(COMMON)
    } :data

    __kernel_end = .;
}

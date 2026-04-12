ENTRY(_start)

PHDRS
{
  text PT_LOAD FLAGS(5);
}

SECTIONS
{
  . = 0;

  .text : ALIGN(16)
  {
    *(.text*)
    *(.rodata*)
  } :text

  /DISCARD/ :
  {
    *(.data*)
    *(.bss*)
    *(.comment*)
    *(.eh_frame*)
    *(.note*)
    *(.note.*)
  }
}

ENTRY(_start)

PHDRS
{
  text PT_LOAD FLAGS(5);
  data PT_LOAD FLAGS(6);
}

SECTIONS
{
  . = 0;

  .text : ALIGN(0x1000)
  {
    *(.text*)
    *(.rodata*)
  } :text

  . = ALIGN(0x1000);

  .data :
  {
    *(.data*)
  } :data

  .bss (NOLOAD) :
  {
    *(.bss*)
    *(COMMON)
  } :data

  /DISCARD/ :
  {
    *(.comment*)
    *(.eh_frame*)
    *(.note*)
    *(.note.*)
  }
}

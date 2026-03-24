from khal import get_idt_base
from khal import get_isr0_addr
from khal import get_isr8_addr
from khal import get_isr13_addr
from khal import get_isr14_addr
from khal import get_isr32_addr
from khal import load_idt_local
from khal import set_idt_gate_asm
from khal import set_idtr_asm


def set_idt_gate(index: int, handler: int, ist: int):
    set_idt_gate_asm(index, handler, ist)


def init_idt():
    set_idt_gate(0, get_isr0_addr(), 0)
    set_idt_gate(8, get_isr8_addr(), 1)
    set_idt_gate(13, get_isr13_addr(), 0)
    set_idt_gate(14, get_isr14_addr(), 0)
    set_idt_gate(32, get_isr32_addr(), 0)

    set_idtr_asm(256 * 16 - 1, get_idt_base())
    load_idt_local()

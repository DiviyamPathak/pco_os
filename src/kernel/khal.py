from C import serial_init()
from C import serial_write_byte(byte)
from C import serial_write_u64(int)
from C import serial_write_hex(int)
from C import set_active_scheduler_asm(int)
from C import get_active_scheduler_asm() -> int
from C import context_switch_asm(int, int)
from C import restore_task_context_asm(int)
from C import get_task_trampoline_addr_asm() -> int
from C import get_user_task_trampoline_addr_asm() -> int
from C import get_user_demo_entry_addr_asm() -> int
from C import enter_user_mode_asm(int, int)
from C import invoke_syscall_asm(int, int, int, int, int, int) -> int
from C import seq_alloc_atomic(int) -> int
from C import seq_terminate()
from C import arch_init()
from C import load_idt_local()
from C import read_cr2() -> int
from C import read_cr3() -> int
from C import load_cr3(int)
from C import read_apic_id() -> int
from C import cpu_has_apic() -> int
from C import read_msr_asm(int) -> int
from C import write_msr_asm(int, int)
from C import load_dword_asm(int) -> int
from C import store_dword_asm(int, int)
from C import outb_asm(int, int)
from C import enable_interrupts()
from C import disable_interrupts()
from C import halt_cpu()
from C import wait_for_interrupt()
from C import set_lapic_eoi_reg_asm(int)
from C import read_timer_irq_count_asm() -> int
from C import clear_timer_irq_count_asm()
from C import get_idt_base() -> int
from C import get_idtr_base() -> int
from C import set_idt_gate_asm(int, int, int)
from C import set_idt_gate_user_asm(int, int, int)
from C import set_idtr_asm(int, int)
from C import set_tss_rsp0_asm(int)
from C import frame_qword_asm(int, int) -> int
from C import store_qword_asm(int, int, int)
from C import get_isr0_addr() -> int
from C import get_isr8_addr() -> int
from C import get_isr13_addr() -> int
from C import get_isr14_addr() -> int
from C import get_isr32_addr() -> int
from C import get_isr128_addr() -> int
from C import trigger_interrupt0()
from C import trigger_divide_error()
from C import trigger_general_protection()
from C import trigger_page_fault()


def frame_qword(base_ptr: int, slot: int):
    return frame_qword_asm(base_ptr, slot)


def store_qword(base_ptr: int, slot: int, value: int):
    store_qword_asm(base_ptr, slot, value)


def read_msr(msr: int):
    return read_msr_asm(msr)


def write_msr(msr: int, value: int):
    write_msr_asm(msr, value)


def load_dword(addr: int):
    return load_dword_asm(addr)


def store_dword(addr: int, value: int):
    store_dword_asm(addr, value)


def outb(port: int, value: int):
    outb_asm(port, value)


def set_lapic_eoi_reg(addr: int):
    set_lapic_eoi_reg_asm(addr)


def read_timer_irq_count():
    return read_timer_irq_count_asm()


def clear_timer_irq_count():
    clear_timer_irq_count_asm()


def set_active_scheduler(addr: int):
    set_active_scheduler_asm(addr)


def get_active_scheduler():
    return get_active_scheduler_asm()


def context_switch(old_ctx_ptr: int, new_ctx_ptr: int):
    context_switch_asm(old_ctx_ptr, new_ctx_ptr)


def restore_task_context(ctx_ptr: int):
    restore_task_context_asm(ctx_ptr)


def task_trampoline_addr():
    return get_task_trampoline_addr_asm()


def user_task_trampoline_addr():
    return get_user_task_trampoline_addr_asm()


def user_demo_entry_addr():
    return get_user_demo_entry_addr_asm()


def enter_user_mode(user_rip: int, user_rsp: int):
    enter_user_mode_asm(user_rip, user_rsp)


def invoke_syscall(number: int, a0: int, a1: int, a2: int, a3: int, a4: int):
    return invoke_syscall_asm(number, a0, a1, a2, a3, a4)


def set_idt_gate_user(index: int, handler: int, ist: int):
    set_idt_gate_user_asm(index, handler, ist)


def set_tss_rsp0(addr: int):
    set_tss_rsp0_asm(addr)

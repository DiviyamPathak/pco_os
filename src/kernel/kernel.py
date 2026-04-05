from khal import arch_init
from khal import get_idt_base
from khal import get_idtr_base
from khal import serial_init
from kapic import arm_timer_masked
from kapic import dump_local_apic_summary
from kapic import dump_timer_summary
from kapic import init_local_apic
from kapic import probe_timer_progress
from kapic import probe_timer_interrupts
from kboot import dump_boot_info
from kconsole import console_write
from kconsole import console_write_hex
from kconsole import console_write_u64
from kconsole import init_console
from kconsole import print_msg
from kexceptions import handle_exception
from kexceptions import run_exception_test
from kidt import init_idt
from ksched import dump_scheduler_summary
from ksched import init_scheduler
from ksched import scheduler_idle_loop
from ksched import scheduler_self_test
from ksyscall import syscall_self_test
from ktime import start_kernel_tick_source
from ktime import timekeeping_self_test
from kmemory import dump_pmm_summary
from kmemory import dump_vmm_summary
from kmemory import init_pmm
from kmemory import init_vmm
from kmemory import pmm_self_test
from kmemory import vmm_self_test


@export
def isr_dispatch(frame: int, vector: int, error_code: int):
    handle_exception(frame, vector, error_code)


@export
def kernel_main(boot_info_ptr: int):
    exception_test = 0
    lapic_timer_count = 10000000
    lapic_tick_reload = 1000000
    serial_init()
    init_console()
    arch_init()
    init_idt()
    console_write("Hello from Codon over serial!\n".c_str())
    console_write("idt base=".c_str())
    console_write_hex(get_idt_base())
    console_write(" idtr=".c_str())
    console_write_hex(get_idtr_base())
    console_write("\n".c_str())
    console_write("boot marker: ".c_str())
    console_write_hex(0xC0D0)
    console_write(" build=".c_str())
    console_write_u64(1)
    console_write("\n".c_str())
    dump_boot_info(boot_info_ptr)
    pmm_state = init_pmm(boot_info_ptr)
    dump_pmm_summary(pmm_state)
    pmm_self_test(pmm_state)
    vmm_state = init_vmm(pmm_state, boot_info_ptr)
    dump_vmm_summary(vmm_state)
    vmm_self_test(vmm_state, pmm_state, boot_info_ptr)
    print_msg("PCO/OS console online".c_str(), 0, 0x0A)
    run_exception_test(exception_test)
    init_local_apic()
    dump_local_apic_summary()
    arm_timer_masked(lapic_timer_count)
    dump_timer_summary()
    probe_timer_progress()
    probe_timer_interrupts(lapic_tick_reload, 3)
    start_kernel_tick_source(lapic_tick_reload)
    timekeeping_self_test(5)
    scheduler_state = init_scheduler()
    dump_scheduler_summary(scheduler_state)
    syscall_self_test()
    dump_scheduler_summary(scheduler_state)
    scheduler_self_test(scheduler_state, 5)
    scheduler_idle_loop(scheduler_state)

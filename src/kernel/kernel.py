from khal import arch_init
from khal import get_idt_base
from khal import get_idtr_base
from khal import halt_cpu
from khal import serial_init
from khal import serial_write_hex
from khal import serial_write_u64
from kapic import arm_timer_masked
from kapic import dump_local_apic_summary
from kapic import dump_timer_summary
from kapic import init_local_apic
from kapic import probe_timer_progress
from kboot import dump_boot_info
from kconsole import serial_write
from kexceptions import handle_exception
from kexceptions import run_exception_test
from kidt import init_idt
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
    serial_init()
    arch_init()
    init_idt()
    serial_write("Hello from Codon over serial!\n".c_str())
    serial_write("idt base=".c_str())
    serial_write_hex(get_idt_base())
    serial_write(" idtr=".c_str())
    serial_write_hex(get_idtr_base())
    serial_write("\n".c_str())
    serial_write("boot marker: ".c_str())
    serial_write_hex(0xC0D0)
    serial_write(" build=".c_str())
    serial_write_u64(1)
    serial_write("\n".c_str())
    dump_boot_info(boot_info_ptr)
    pmm_state = init_pmm(boot_info_ptr)
    dump_pmm_summary(pmm_state)
    pmm_self_test(pmm_state)
    vmm_state = init_vmm(pmm_state, boot_info_ptr)
    dump_vmm_summary(vmm_state)
    vmm_self_test(vmm_state, pmm_state, boot_info_ptr)
    run_exception_test(exception_test)
    init_local_apic()
    dump_local_apic_summary()
    arm_timer_masked(lapic_timer_count)
    dump_timer_summary()
    probe_timer_progress()

    while True:
        halt_cpu()

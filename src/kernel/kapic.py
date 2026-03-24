from khal import cpu_has_apic
from khal import clear_timer_irq_count
from khal import load_dword
from khal import outb
from khal import read_timer_irq_count
from khal import read_msr
from khal import set_lapic_eoi_reg
from khal import store_dword
from khal import write_msr
from kconsole import serial_write_label_hex
from kconsole import serial_write_label_u64
from kconsole import serial_write_line
from ksupport import panic


def lapic_base():
    base = read_msr(0x1B)
    if (base & (1 << 11)) == 0:
        write_msr(0x1B, base | (1 << 11))
        base = read_msr(0x1B)
    return base & ~0xFFF


def lapic_read(offset: int):
    return load_dword(lapic_base() + offset)


def lapic_write(offset: int, value: int):
    store_dword(lapic_base() + offset, value)


def mask_legacy_pic():
    outb(0x21, 0xFF)
    outb(0xA1, 0xFF)


def init_local_apic():
    if cpu_has_apic() == 0:
        panic("cpu has no local apic".c_str())

    mask_legacy_pic()
    set_lapic_eoi_reg(lapic_base() + 0xB0)
    lapic_write(0x80, 0)
    lapic_write(0x350, 1 << 16)
    lapic_write(0x360, 1 << 16)
    lapic_write(0xF0, 0x1FF)


def dump_local_apic_summary():
    serial_write_label_hex("lapic.base=".c_str(), lapic_base())
    serial_write_label_u64("lapic.version=".c_str(), lapic_read(0x30) & 0xFF)
    serial_write_label_u64("lapic.id=".c_str(), lapic_read(0x20) >> 24)


def arm_timer_oneshot(initial_count: int):
    if initial_count == 0:
        panic("lapic timer count is zero".c_str())

    lapic_write(0x3E0, 0x3)
    lapic_write(0x320, 32)
    lapic_write(0x380, initial_count)


def arm_timer_masked(initial_count: int):
    if initial_count == 0:
        panic("lapic timer count is zero".c_str())

    lapic_write(0x3E0, 0x3)
    lapic_write(0x320, 32 | (1 << 16))
    lapic_write(0x380, initial_count)


def dump_timer_summary():
    serial_write_label_u64("lapic.timer.divide=".c_str(), lapic_read(0x3E0) & 0xF)
    serial_write_label_hex("lapic.timer.initial=".c_str(), lapic_read(0x380))
    serial_write_label_hex("lapic.timer.current=".c_str(), lapic_read(0x390))


def timer_current_count():
    return lapic_read(0x390)


def probe_timer_progress():
    start = timer_current_count()
    tries = 0

    while tries < 1000000:
        current = timer_current_count()
        if current != start:
            serial_write_label_hex("lapic.timer.probe.start=".c_str(), start)
            serial_write_label_hex("lapic.timer.probe.current=".c_str(), current)
            if current < start:
                serial_write_line("lapic timer probe ok".c_str())
                return
            break
        tries += 1

    panic("lapic timer probe failed".c_str())


def timer_tick_count():
    return read_timer_irq_count()


def reset_timer_ticks():
    clear_timer_irq_count()

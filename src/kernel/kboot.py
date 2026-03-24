from khal import frame_qword
from khal import read_apic_id
from kconsole import serial_write
from kconsole import serial_write_hex
from kconsole import serial_write_label_hex
from kconsole import serial_write_label_u64
from kconsole import serial_write_line
from kconsole import serial_write_u64
from ksupport import panic


def boot_info_qword(boot_info_ptr: int, slot: int):
    return frame_qword(boot_info_ptr, slot)


def dump_boot_memory_map(boot_info_ptr: int):
    mmap_ptr = boot_info_qword(boot_info_ptr, 3)
    mmap_count = boot_info_qword(boot_info_ptr, 4)

    serial_write_label_hex("boot.mmap.ptr=".c_str(), mmap_ptr)
    serial_write_label_u64("boot.mmap.count=".c_str(), mmap_count)
    if mmap_ptr == 0 or mmap_count == 0:
        serial_write_line("boot memory map unavailable".c_str())
        return

    entry_index = 0
    while entry_index < mmap_count and entry_index < 12:
        entry = mmap_ptr + entry_index * 32
        serial_write("mmap[".c_str())
        serial_write_u64(entry_index)
        serial_write("] base=".c_str())
        serial_write_hex(frame_qword(entry, 0))
        serial_write(" len=".c_str())
        serial_write_hex(frame_qword(entry, 1))
        serial_write(" type=".c_str())
        serial_write_u64(frame_qword(entry, 2))
        serial_write(" attrs=".c_str())
        serial_write_hex(frame_qword(entry, 3))
        serial_write("\n".c_str())
        entry_index += 1


def dump_boot_info(boot_info_ptr: int):
    magic = boot_info_qword(boot_info_ptr, 0)
    version = boot_info_qword(boot_info_ptr, 1)
    boot_method = boot_info_qword(boot_info_ptr, 2)

    serial_write_label_hex("boot.info.ptr=".c_str(), boot_info_ptr)
    serial_write_label_hex("boot.info.magic=".c_str(), magic)
    serial_write_label_u64("boot.info.version=".c_str(), version)
    if magic != 0x50434F424F4F5431:
        panic("boot info magic mismatch".c_str())

    serial_write("boot.method=".c_str())
    if boot_method == 1:
        serial_write_line("multiboot-fallback".c_str())
    elif boot_method == 2:
        serial_write_line("uefi-loader".c_str())
    else:
        serial_write("unknown ".c_str())
        serial_write_u64(boot_method)
        serial_write("\n".c_str())

    serial_write_label_hex("boot.kernel.phys.start=".c_str(), boot_info_qword(boot_info_ptr, 13))
    serial_write_label_hex("boot.kernel.phys.end=".c_str(), boot_info_qword(boot_info_ptr, 14))
    serial_write_label_hex("boot.kernel.virt.start=".c_str(), boot_info_qword(boot_info_ptr, 15))
    serial_write_label_hex("boot.kernel.virt.end=".c_str(), boot_info_qword(boot_info_ptr, 16))
    serial_write_label_u64("boot.cpu.count_hint=".c_str(), boot_info_qword(boot_info_ptr, 18))
    serial_write_label_u64("boot.cpu.current_apic=".c_str(), read_apic_id())
    serial_write_label_hex("boot.raw.ptr=".c_str(), boot_info_qword(boot_info_ptr, 19))
    serial_write_label_hex("boot.raw.magic=".c_str(), boot_info_qword(boot_info_ptr, 20))
    dump_boot_memory_map(boot_info_ptr)

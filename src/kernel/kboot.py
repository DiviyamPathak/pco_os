from khal import read_apic_id
from kconsole import console_write
from kconsole import console_write_hex
from kconsole import console_write_label_hex
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from ksupport import load_qword_region
from ksupport import panic


def boot_info_qword(boot_info_ptr: int, slot: int):
    return load_qword_region(boot_info_ptr, 23, slot)


def boot_memory_map_qword(entry_ptr: int, slot: int):
    return load_qword_region(entry_ptr, 4, slot)


def dump_boot_memory_map(boot_info_ptr: int):
    mmap_ptr = boot_info_qword(boot_info_ptr, 3)
    mmap_count = boot_info_qword(boot_info_ptr, 4)

    console_write_label_hex("boot.mmap.ptr=".c_str(), mmap_ptr)
    console_write_label_u64("boot.mmap.count=".c_str(), mmap_count)
    if mmap_ptr == 0 or mmap_count == 0:
        console_write_line("boot memory map unavailable".c_str())
        return

    entry_index = 0
    while entry_index < mmap_count and entry_index < 12:
        entry = mmap_ptr + entry_index * 32
        console_write("mmap[".c_str())
        console_write_u64(entry_index)
        console_write("] base=".c_str())
        console_write_hex(boot_memory_map_qword(entry, 0))
        console_write(" len=".c_str())
        console_write_hex(boot_memory_map_qword(entry, 1))
        console_write(" type=".c_str())
        console_write_u64(boot_memory_map_qword(entry, 2))
        console_write(" attrs=".c_str())
        console_write_hex(boot_memory_map_qword(entry, 3))
        console_write("\n".c_str())
        entry_index += 1


def dump_boot_info(boot_info_ptr: int):
    magic = boot_info_qword(boot_info_ptr, 0)
    version = boot_info_qword(boot_info_ptr, 1)
    boot_method = boot_info_qword(boot_info_ptr, 2)

    console_write_label_hex("boot.info.ptr=".c_str(), boot_info_ptr)
    console_write_label_hex("boot.info.magic=".c_str(), magic)
    console_write_label_u64("boot.info.version=".c_str(), version)
    if magic != 0x50434F424F4F5431:
        panic("boot info magic mismatch".c_str())

    console_write("boot.method=".c_str())
    if boot_method == 1:
        console_write_line("multiboot-fallback".c_str())
    elif boot_method == 2:
        console_write_line("uefi-loader".c_str())
    else:
        console_write("unknown ".c_str())
        console_write_u64(boot_method)
        console_write("\n".c_str())

    console_write_label_hex("boot.kernel.phys.start=".c_str(), boot_info_qword(boot_info_ptr, 13))
    console_write_label_hex("boot.kernel.phys.end=".c_str(), boot_info_qword(boot_info_ptr, 14))
    console_write_label_hex("boot.kernel.virt.start=".c_str(), boot_info_qword(boot_info_ptr, 15))
    console_write_label_hex("boot.kernel.virt.end=".c_str(), boot_info_qword(boot_info_ptr, 16))
    console_write_label_u64("boot.cpu.count_hint=".c_str(), boot_info_qword(boot_info_ptr, 18))
    console_write_label_u64("boot.cpu.current_apic=".c_str(), read_apic_id())
    console_write_label_hex("boot.raw.ptr=".c_str(), boot_info_qword(boot_info_ptr, 19))
    console_write_label_hex("boot.raw.magic=".c_str(), boot_info_qword(boot_info_ptr, 20))
    console_write_label_hex("boot.initramfs.ptr=".c_str(), boot_info_qword(boot_info_ptr, 21))
    console_write_label_u64("boot.initramfs.size=".c_str(), boot_info_qword(boot_info_ptr, 22))
    dump_boot_memory_map(boot_info_ptr)

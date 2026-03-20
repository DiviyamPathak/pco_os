from C import serial_init()
from C import serial_write_byte(byte)
from C import serial_write_u64(int)
from C import serial_write_hex(int)
from C import seq_terminate()
from C import arch_init()
from C import load_idt_local()
from C import read_cr2() -> int
from C import read_apic_id() -> int
from C import get_idt_base() -> int
from C import get_idtr_base() -> int
from C import set_idt_gate_asm(int, int, int)
from C import set_idtr_asm(int, int)
from C import frame_qword_asm(int, int) -> int
from C import get_isr0_addr() -> int
from C import get_isr8_addr() -> int
from C import get_isr13_addr() -> int
from C import get_isr14_addr() -> int
from C import trigger_interrupt0()
from C import trigger_divide_error()
from C import trigger_general_protection()
from C import trigger_page_fault()


def print_msg(msg: cobj, line: int, color: int):
    video_memory = Ptr[byte](0xB8000)
    i = 0
    while msg[i] != byte(0):
        video_memory[(line * 80 + i) * 2] = msg[i]
        video_memory[(line * 80 + i) * 2 + 1] = byte(color)
        i += 1


def serial_write(msg: cobj):
    i = 0
    while msg[i] != byte(0):
        if msg[i] == byte(10):
            serial_write_byte(byte(13))
        serial_write_byte(msg[i])
        i += 1


def serial_write_line(msg: cobj):
    serial_write(msg)
    serial_write("\n".c_str())


def read_u32(addr: int):
    data = Ptr[byte](addr)
    return (
        int(data[0])
        | (int(data[1]) << 8)
        | (int(data[2]) << 16)
        | (int(data[3]) << 24)
    )


def read_u64(addr: int):
    low = read_u32(addr)
    high = read_u32(addr + 4)
    return low | (high << 32)


def serial_write_label_hex(label: cobj, value: int):
    serial_write(label)
    serial_write_hex(value)
    serial_write("\n".c_str())


def serial_write_label_u64(label: cobj, value: int):
    serial_write(label)
    serial_write_u64(value)
    serial_write("\n".c_str())


def set_idt_gate(index: int, handler: int, ist: int):
    set_idt_gate_asm(index, handler, ist)


def init_idt():
    set_idt_gate(0, get_isr0_addr(), 0)
    set_idt_gate(8, get_isr8_addr(), 1)
    set_idt_gate(13, get_isr13_addr(), 0)
    set_idt_gate(14, get_isr14_addr(), 0)

    set_idtr_asm(256 * 16 - 1, get_idt_base())
    load_idt_local()


def run_exception_test(mode: int):
    if mode == 0:
        return

    serial_write_line("running exception test".c_str())
    if mode == 1:
        serial_write_line("mode=int0".c_str())
        trigger_interrupt0()

    if mode == 2:
        serial_write_line("mode=de".c_str())
        trigger_divide_error()

    if mode == 3:
        serial_write_line("mode=gp".c_str())
        trigger_general_protection()

    if mode == 4:
        serial_write_line("mode=pf".c_str())
        trigger_page_fault()

    panic("unknown exception test".c_str())


def frame_qword(frame: int, slot: int):
    return frame_qword_asm(frame, slot)


def boot_info_qword(boot_info_ptr: int, slot: int):
    return frame_qword_asm(boot_info_ptr, slot)


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
        serial_write_hex(frame_qword_asm(entry, 0))
        serial_write(" len=".c_str())
        serial_write_hex(frame_qword_asm(entry, 1))
        serial_write(" type=".c_str())
        serial_write_u64(frame_qword_asm(entry, 2))
        serial_write(" attrs=".c_str())
        serial_write_hex(frame_qword_asm(entry, 3))
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


def serial_write_register(name: cobj, value: int):
    serial_write(name)
    serial_write("=".c_str())
    serial_write_hex(value)
    serial_write("\n".c_str())


def serial_write_exception_name(vector: int):
    if vector == 0:
        serial_write(" (#DE divide error)".c_str())
        return
    if vector == 8:
        serial_write(" (#DF double fault)".c_str())
        return
    if vector == 13:
        serial_write(" (#GP general protection)".c_str())
        return
    if vector == 14:
        serial_write(" (#PF page fault)".c_str())
        return


def serial_write_page_fault_bits(error_code: int):
    serial_write("pf bits:".c_str())
    if (error_code & 1) != 0:
        serial_write(" P".c_str())
    else:
        serial_write(" NP".c_str())
    if (error_code & 2) != 0:
        serial_write(" WRITE".c_str())
    else:
        serial_write(" READ".c_str())
    if (error_code & 4) != 0:
        serial_write(" USER".c_str())
    else:
        serial_write(" KERNEL".c_str())
    if (error_code & 8) != 0:
        serial_write(" RSVD".c_str())
    if (error_code & 16) != 0:
        serial_write(" IFETCH".c_str())
    serial_write("\n".c_str())


def panic(msg: cobj):
    serial_write("panic: ".c_str())
    serial_write_line(msg)
    seq_terminate()


@export
def isr_dispatch(frame: int, vector: int, error_code: int):
    serial_write("\nexception cpu=".c_str())
    serial_write_u64(read_apic_id())
    serial_write(" vector=".c_str())
    serial_write_u64(vector)
    serial_write_exception_name(vector)
    serial_write(" error=".c_str())
    serial_write_hex(error_code)
    serial_write("\n".c_str())

    if vector == 14:
        serial_write("cr2=".c_str())
        serial_write_hex(read_cr2())
        serial_write("\n".c_str())
        serial_write_page_fault_bits(error_code)

    serial_write_register("rip".c_str(), frame_qword(frame, 17))
    serial_write_register("cs".c_str(), frame_qword(frame, 18))
    serial_write_register("rflags".c_str(), frame_qword(frame, 19))
    serial_write_register("rax".c_str(), frame_qword(frame, 0))
    serial_write_register("rbx".c_str(), frame_qword(frame, 1))
    serial_write_register("rcx".c_str(), frame_qword(frame, 2))
    serial_write_register("rdx".c_str(), frame_qword(frame, 3))
    serial_write_register("rsi".c_str(), frame_qword(frame, 4))
    serial_write_register("rdi".c_str(), frame_qword(frame, 5))
    serial_write_register("rbp".c_str(), frame_qword(frame, 6))
    serial_write_register("r8".c_str(), frame_qword(frame, 7))
    serial_write_register("r9".c_str(), frame_qword(frame, 8))
    serial_write_register("r10".c_str(), frame_qword(frame, 9))
    serial_write_register("r11".c_str(), frame_qword(frame, 10))
    serial_write_register("r12".c_str(), frame_qword(frame, 11))
    serial_write_register("r13".c_str(), frame_qword(frame, 12))
    serial_write_register("r14".c_str(), frame_qword(frame, 13))
    serial_write_register("r15".c_str(), frame_qword(frame, 14))

    seq_terminate()


@export
def kernel_main(boot_info_ptr: int):
    exception_test = 0
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
    run_exception_test(exception_test)

    while True:
        pass

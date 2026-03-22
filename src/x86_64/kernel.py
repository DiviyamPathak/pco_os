from C import serial_init()
from C import serial_write_byte(byte)
from C import serial_write_u64(int)
from C import serial_write_hex(int)
from C import seq_alloc_atomic(int) -> int
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
from C import store_qword_asm(int, int, int)
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


def align_down(value: int, align: int):
    return value & ~(align - 1)


def align_up(value: int, align: int):
    return (value + align - 1) & ~(align - 1)


def alloc_bytes(size: int):
    addr = seq_alloc_atomic(size)
    if addr == 0:
        panic("early heap exhausted".c_str())
    return addr


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


def pmm_state_qword(state_ptr: int, slot: int):
    return frame_qword_asm(state_ptr, slot)


def set_pmm_state_qword(state_ptr: int, slot: int, value: int):
    store_qword_asm(state_ptr, slot, value)


def pmm_region_start(region_table_ptr: int, index: int):
    return frame_qword_asm(region_table_ptr + index * 16, 0)


def pmm_region_end(region_table_ptr: int, index: int):
    return frame_qword_asm(region_table_ptr + index * 16, 1)


def set_pmm_region(region_table_ptr: int, index: int, start: int, end: int):
    entry_ptr = region_table_ptr + index * 16
    store_qword_asm(entry_ptr, 0, start)
    store_qword_asm(entry_ptr, 1, end)


def pmm_stack_push(stack_ptr: int, index: int, value: int):
    store_qword_asm(stack_ptr, index, value)


def pmm_stack_pop(stack_ptr: int, index: int):
    return frame_qword_asm(stack_ptr, index)


def pmm_add_region(state_ptr: int, start: int, end: int):
    if start >= end:
        return

    pages = (end - start) >> 12
    if pages == 0:
        return

    region_count = pmm_state_qword(state_ptr, 1)
    if region_count >= 64:
        panic("pmm region table full".c_str())

    region_table_ptr = pmm_state_qword(state_ptr, 0)
    set_pmm_region(region_table_ptr, region_count, start, end)
    set_pmm_state_qword(state_ptr, 1, region_count + 1)
    set_pmm_state_qword(state_ptr, 5, pmm_state_qword(state_ptr, 5) + pages)
    set_pmm_state_qword(state_ptr, 6, pmm_state_qword(state_ptr, 6) + pages)


def init_pmm(boot_info_ptr: int):
    mmap_ptr = boot_info_qword(boot_info_ptr, 3)
    mmap_count = boot_info_qword(boot_info_ptr, 4)
    kernel_start = align_down(boot_info_qword(boot_info_ptr, 13), 4096)
    kernel_end = align_up(boot_info_qword(boot_info_ptr, 14), 4096)
    state_ptr = alloc_bytes(7 * 8)
    region_table_ptr = alloc_bytes(64 * 16)
    recycle_stack_ptr = alloc_bytes(2048 * 8)

    if mmap_ptr == 0 or mmap_count == 0:
        panic("pmm requires a boot memory map".c_str())

    set_pmm_state_qword(state_ptr, 0, region_table_ptr)
    set_pmm_state_qword(state_ptr, 1, 0)
    set_pmm_state_qword(state_ptr, 2, 0)
    set_pmm_state_qword(state_ptr, 3, recycle_stack_ptr)
    set_pmm_state_qword(state_ptr, 4, 0)
    set_pmm_state_qword(state_ptr, 5, 0)
    set_pmm_state_qword(state_ptr, 6, 0)

    entry_index = 0
    while entry_index < mmap_count:
        entry = mmap_ptr + entry_index * 32
        base = frame_qword_asm(entry, 0)
        length = frame_qword_asm(entry, 1)
        entry_type = frame_qword_asm(entry, 2)

        if entry_type == 7 and length != 0:
            start = align_up(base, 4096)
            end = align_down(base + length, 4096)

            if end > 0x100000:
                if start < 0x100000:
                    start = 0x100000

                if start < kernel_start and end > kernel_start:
                    pmm_add_region(state_ptr, start, kernel_start)
                    start = kernel_end
                elif start >= kernel_start and start < kernel_end:
                    start = kernel_end

                if start < end:
                    pmm_add_region(state_ptr, start, end)

        entry_index += 1

    if pmm_state_qword(state_ptr, 1) == 0:
        panic("pmm found no usable regions".c_str())

    return state_ptr


def pmm_alloc_page(state_ptr: int):
    free_pages = pmm_state_qword(state_ptr, 6)
    if free_pages == 0:
        return 0

    recycle_count = pmm_state_qword(state_ptr, 4)
    if recycle_count != 0:
        recycle_count -= 1
        stack_ptr = pmm_state_qword(state_ptr, 3)
        page = pmm_stack_pop(stack_ptr, recycle_count)
        set_pmm_state_qword(state_ptr, 4, recycle_count)
        set_pmm_state_qword(state_ptr, 6, free_pages - 1)
        return page

    region_index = pmm_state_qword(state_ptr, 2)
    region_count = pmm_state_qword(state_ptr, 1)
    region_table_ptr = pmm_state_qword(state_ptr, 0)

    while region_index < region_count:
        start = pmm_region_start(region_table_ptr, region_index)
        end = pmm_region_end(region_table_ptr, region_index)

        if start + 4096 <= end:
            next_page = start + 4096
            set_pmm_region(region_table_ptr, region_index, next_page, end)
            if next_page >= end:
                set_pmm_state_qword(state_ptr, 2, region_index + 1)
            set_pmm_state_qword(state_ptr, 6, free_pages - 1)
            return start

        region_index += 1
        set_pmm_state_qword(state_ptr, 2, region_index)

    return 0


def pmm_free_page(state_ptr: int, page: int):
    if page == 0:
        panic("cannot free null page".c_str())

    if (page & 0xFFF) != 0:
        panic("cannot free unaligned page".c_str())

    recycle_count = pmm_state_qword(state_ptr, 4)
    if recycle_count >= 2048:
        panic("pmm recycle stack full".c_str())

    stack_ptr = pmm_state_qword(state_ptr, 3)
    pmm_stack_push(stack_ptr, recycle_count, page)
    set_pmm_state_qword(state_ptr, 4, recycle_count + 1)
    set_pmm_state_qword(state_ptr, 6, pmm_state_qword(state_ptr, 6) + 1)


def dump_pmm_summary(state_ptr: int):
    serial_write_label_u64("pmm.regions=".c_str(), pmm_state_qword(state_ptr, 1))
    serial_write_label_u64("pmm.total_pages=".c_str(), pmm_state_qword(state_ptr, 5))
    serial_write_label_u64("pmm.free_pages=".c_str(), pmm_state_qword(state_ptr, 6))

    region_table_ptr = pmm_state_qword(state_ptr, 0)
    region_count = pmm_state_qword(state_ptr, 1)
    region_index = 0
    while region_index < region_count and region_index < 8:
        serial_write("pmm.region[".c_str())
        serial_write_u64(region_index)
        serial_write("] start=".c_str())
        serial_write_hex(pmm_region_start(region_table_ptr, region_index))
        serial_write(" end=".c_str())
        serial_write_hex(pmm_region_end(region_table_ptr, region_index))
        serial_write("\n".c_str())
        region_index += 1


def pmm_self_test(state_ptr: int):
    free_before = pmm_state_qword(state_ptr, 6)
    page0 = pmm_alloc_page(state_ptr)
    page1 = pmm_alloc_page(state_ptr)
    page2 = pmm_alloc_page(state_ptr)

    if page0 == 0 or page1 == 0 or page2 == 0:
        panic("pmm alloc failed".c_str())

    if page0 == page1 or page0 == page2 or page1 == page2:
        panic("pmm returned duplicate pages".c_str())

    if (page0 & 0xFFF) != 0 or (page1 & 0xFFF) != 0 or (page2 & 0xFFF) != 0:
        panic("pmm returned unaligned page".c_str())

    serial_write_label_hex("pmm.test.page0=".c_str(), page0)
    serial_write_label_hex("pmm.test.page1=".c_str(), page1)
    serial_write_label_hex("pmm.test.page2=".c_str(), page2)

    pmm_free_page(state_ptr, page2)
    pmm_free_page(state_ptr, page1)
    pmm_free_page(state_ptr, page0)

    if pmm_state_qword(state_ptr, 6) != free_before:
        panic("pmm free count mismatch".c_str())

    serial_write_line("pmm self-test ok".c_str())


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
    pmm_state = init_pmm(boot_info_ptr)
    dump_pmm_summary(pmm_state)
    pmm_self_test(pmm_state)
    run_exception_test(exception_test)

    while True:
        pass

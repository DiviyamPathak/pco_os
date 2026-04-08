from khal import frame_qword
from khal import load_byte
from khal import load_dword
from khal import seq_alloc_atomic
from khal import seq_terminate
from khal import store_byte
from khal import store_dword
from khal import store_qword
from kconsole import console_write
from kconsole import console_write_hex
from kconsole import console_write_line
from kconsole import console_write_u64


def align_down(value: int, align: int):
    return value & ~(align - 1)


def align_up(value: int, align: int):
    return (value + align - 1) & ~(align - 1)


def panic(msg: cobj):
    console_write("panic: ".c_str())
    console_write_line(msg)
    seq_terminate()


def panic_region_access(msg: cobj, base_ptr: int, index: int, limit: int):
    console_write("panic: ".c_str())
    console_write_line(msg)
    console_write("base=".c_str())
    console_write_hex(base_ptr)
    console_write("\n".c_str())
    console_write("index=".c_str())
    console_write_u64(index)
    console_write("\n".c_str())
    console_write("limit=".c_str())
    console_write_u64(limit)
    console_write("\n".c_str())
    seq_terminate()


def load_qword_region(base_ptr: int, qword_count: int, slot: int):
    if base_ptr == 0:
        panic("qword region base is null".c_str())
    if (base_ptr & 0x7) != 0:
        panic("qword region base is unaligned".c_str())
    if qword_count <= 0:
        panic("qword region is empty".c_str())
    if slot < 0 or slot >= qword_count:
        panic_region_access("qword slot out of range".c_str(), base_ptr, slot, qword_count)
    return frame_qword(base_ptr, slot)


def store_qword_region(base_ptr: int, qword_count: int, slot: int, value: int):
    if base_ptr == 0:
        panic("qword region base is null".c_str())
    if (base_ptr & 0x7) != 0:
        panic("qword region base is unaligned".c_str())
    if qword_count <= 0:
        panic("qword region is empty".c_str())
    if slot < 0 or slot >= qword_count:
        panic_region_access("qword slot out of range".c_str(), base_ptr, slot, qword_count)
    store_qword(base_ptr, slot, value)


def load_dword_region(base_ptr: int, byte_count: int, offset: int):
    if base_ptr == 0:
        panic("dword region base is null".c_str())
    if (base_ptr & 0x3) != 0:
        panic("dword region base is unaligned".c_str())
    if byte_count < 4:
        panic("dword region is too small".c_str())
    if (offset & 0x3) != 0:
        panic("dword region offset is unaligned".c_str())
    if offset < 0 or offset + 4 > byte_count:
        panic_region_access("dword offset out of range".c_str(), base_ptr, offset, byte_count)
    return load_dword(base_ptr + offset)


def load_byte_region(base_ptr: int, byte_count: int, offset: int):
    if base_ptr == 0:
        panic("byte region base is null".c_str())
    if byte_count <= 0:
        panic("byte region is empty".c_str())
    if offset < 0 or offset >= byte_count:
        panic_region_access("byte offset out of range".c_str(), base_ptr, offset, byte_count)
    return load_byte(base_ptr + offset)


def store_dword_region(base_ptr: int, byte_count: int, offset: int, value: int):
    if base_ptr == 0:
        panic("dword region base is null".c_str())
    if (base_ptr & 0x3) != 0:
        panic("dword region base is unaligned".c_str())
    if byte_count < 4:
        panic("dword region is too small".c_str())
    if (offset & 0x3) != 0:
        panic("dword region offset is unaligned".c_str())
    if offset < 0 or offset + 4 > byte_count:
        panic_region_access("dword offset out of range".c_str(), base_ptr, offset, byte_count)
    store_dword(base_ptr + offset, value)


def store_byte_region(base_ptr: int, byte_count: int, offset: int, value: int):
    if base_ptr == 0:
        panic("byte region base is null".c_str())
    if byte_count <= 0:
        panic("byte region is empty".c_str())
    if offset < 0 or offset >= byte_count:
        panic_region_access("byte offset out of range".c_str(), base_ptr, offset, byte_count)
    store_byte(base_ptr + offset, value)


def alloc_bytes(size: int):
    addr = seq_alloc_atomic(size)
    if addr == 0:
        panic("early heap exhausted".c_str())
    return addr

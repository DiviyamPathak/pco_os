from khal import seq_alloc_atomic
from khal import seq_terminate
from kconsole import serial_write
from kconsole import serial_write_line


def align_down(value: int, align: int):
    return value & ~(align - 1)


def align_up(value: int, align: int):
    return (value + align - 1) & ~(align - 1)


def panic(msg: cobj):
    serial_write("panic: ".c_str())
    serial_write_line(msg)
    seq_terminate()


def alloc_bytes(size: int):
    addr = seq_alloc_atomic(size)
    if addr == 0:
        panic("early heap exhausted".c_str())
    return addr

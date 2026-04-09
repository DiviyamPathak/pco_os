from khal import serial_read_byte
from khal import serial_rx_ready
from khal import serial_write_byte
from khal import load_byte


def print_msg(msg: cobj, line: int, color: int):
    video_memory = Ptr[byte](0xB8000)
    i = 0
    while msg[i] != byte(0):
        video_memory[(line * 80 + i) * 2] = msg[i]
        video_memory[(line * 80 + i) * 2 + 1] = byte(color)
        i += 1


def init_console():
    pass


def enable_vga_console():
    pass


def console_put_byte(ch: byte):
    if ch == byte(10):
        serial_write_byte(byte(13))
    serial_write_byte(ch)


def console_input_ready():
    return serial_rx_ready() != 0


def console_read_byte():
    return serial_read_byte()


def console_read_ptr_len(ptr: int, length: int):
    dst = Ptr[byte](ptr)
    count = 0

    if ptr == 0 or length <= 0:
        return 0

    while count < length and console_input_ready():
        ch = console_read_byte()
        if ch == 13:
            ch = 10
        dst[count] = byte(ch)
        count += 1
    return count


def console_write(msg: cobj):
    i = 0
    while msg[i] != byte(0):
        console_put_byte(msg[i])
        i += 1


def console_write_ptr(ptr: int):
    i = 0
    while byte(load_byte(ptr + i)) != byte(0):
        console_put_byte(byte(load_byte(ptr + i)))
        i += 1


def console_write_ptr_len(ptr: int, length: int):
    if ptr == 0 or length <= 0:
        return 0

    i = 0
    while i < length:
        console_put_byte(byte(load_byte(ptr + i)))
        i += 1
    return i


def console_write_line(msg: cobj):
    console_write(msg)
    console_write("\n".c_str())


def console_write_u64(value: int):
    if value < 0:
        console_put_byte(byte(45))
        value = -value

    if value >= 10:
        console_write_u64(value // 10)

    console_put_byte(byte(48 + value % 10))


def console_write_hex(value: int):
    shift = 60
    console_put_byte(byte(48))
    console_put_byte(byte(120))
    while shift >= 0:
        nibble = (value >> shift) & 0xF
        if nibble < 10:
            console_put_byte(byte(48 + nibble))
        else:
            console_put_byte(byte(55 + nibble))
        shift -= 4


def console_write_label_hex(label: cobj, value: int):
    console_write(label)
    console_write_hex(value)
    console_write("\n".c_str())


def console_write_label_u64(label: cobj, value: int):
    console_write(label)
    console_write_u64(value)
    console_write("\n".c_str())


def console_write_register(name: cobj, value: int):
    console_write(name)
    console_write("=".c_str())
    console_write_hex(value)
    console_write("\n".c_str())

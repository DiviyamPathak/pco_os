from khal import serial_write_byte
from khal import serial_write_hex
from khal import serial_write_u64


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


def serial_write_label_hex(label: cobj, value: int):
    serial_write(label)
    serial_write_hex(value)
    serial_write("\n".c_str())


def serial_write_label_u64(label: cobj, value: int):
    serial_write(label)
    serial_write_u64(value)
    serial_write("\n".c_str())


def serial_write_register(name: cobj, value: int):
    serial_write(name)
    serial_write("=".c_str())
    serial_write_hex(value)
    serial_write("\n".c_str())

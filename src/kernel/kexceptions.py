from khal import frame_qword
from khal import read_apic_id
from khal import read_cr2
from khal import seq_terminate
from khal import trigger_divide_error
from khal import trigger_general_protection
from khal import trigger_interrupt0
from khal import trigger_page_fault
from kconsole import serial_write
from kconsole import serial_write_hex
from kconsole import serial_write_line
from kconsole import serial_write_register
from kconsole import serial_write_u64
from ksupport import panic


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


def handle_exception(frame: int, vector: int, error_code: int):
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

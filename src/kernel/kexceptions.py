from khal import read_apic_id
from khal import read_cr2
from khal import seq_terminate
from khal import trigger_divide_error
from khal import trigger_general_protection
from khal import trigger_interrupt0
from khal import trigger_page_fault
from kconsole import console_write
from kconsole import console_write_hex
from kconsole import console_write_line
from kconsole import console_write_register
from kconsole import console_write_u64
from ksupport import load_qword_region
from ksupport import panic


def serial_write_exception_name(vector: int):
    if vector == 0:
        console_write(" (#DE divide error)".c_str())
        return
    if vector == 8:
        console_write(" (#DF double fault)".c_str())
        return
    if vector == 13:
        console_write(" (#GP general protection)".c_str())
        return
    if vector == 14:
        console_write(" (#PF page fault)".c_str())
        return


def serial_write_page_fault_bits(error_code: int):
    console_write("pf bits:".c_str())
    if (error_code & 1) != 0:
        console_write(" P".c_str())
    else:
        console_write(" NP".c_str())
    if (error_code & 2) != 0:
        console_write(" WRITE".c_str())
    else:
        console_write(" READ".c_str())
    if (error_code & 4) != 0:
        console_write(" USER".c_str())
    else:
        console_write(" KERNEL".c_str())
    if (error_code & 8) != 0:
        console_write(" RSVD".c_str())
    if (error_code & 16) != 0:
        console_write(" IFETCH".c_str())
    console_write("\n".c_str())


def run_exception_test(mode: int):
    if mode == 0:
        return

    console_write_line("running exception test".c_str())
    if mode == 1:
        console_write_line("mode=int0".c_str())
        trigger_interrupt0()

    if mode == 2:
        console_write_line("mode=de".c_str())
        trigger_divide_error()

    if mode == 3:
        console_write_line("mode=gp".c_str())
        trigger_general_protection()

    if mode == 4:
        console_write_line("mode=pf".c_str())
        trigger_page_fault()

    panic("unknown exception test".c_str())


def exception_frame_qword(frame: int, slot: int):
    return load_qword_region(frame, 20, slot)


def handle_exception(frame: int, vector: int, error_code: int):
    console_write("\nexception cpu=".c_str())
    console_write_u64(read_apic_id())
    console_write(" vector=".c_str())
    console_write_u64(vector)
    serial_write_exception_name(vector)
    console_write(" error=".c_str())
    console_write_hex(error_code)
    console_write("\n".c_str())

    if vector == 14:
        console_write("cr2=".c_str())
        console_write_hex(read_cr2())
        console_write("\n".c_str())
        serial_write_page_fault_bits(error_code)

    console_write_register("rip".c_str(), exception_frame_qword(frame, 17))
    console_write_register("cs".c_str(), exception_frame_qword(frame, 18))
    console_write_register("rflags".c_str(), exception_frame_qword(frame, 19))
    console_write_register("rax".c_str(), exception_frame_qword(frame, 0))
    console_write_register("rbx".c_str(), exception_frame_qword(frame, 1))
    console_write_register("rcx".c_str(), exception_frame_qword(frame, 2))
    console_write_register("rdx".c_str(), exception_frame_qword(frame, 3))
    console_write_register("rsi".c_str(), exception_frame_qword(frame, 4))
    console_write_register("rdi".c_str(), exception_frame_qword(frame, 5))
    console_write_register("rbp".c_str(), exception_frame_qword(frame, 6))
    console_write_register("r8".c_str(), exception_frame_qword(frame, 7))
    console_write_register("r9".c_str(), exception_frame_qword(frame, 8))
    console_write_register("r10".c_str(), exception_frame_qword(frame, 9))
    console_write_register("r11".c_str(), exception_frame_qword(frame, 10))
    console_write_register("r12".c_str(), exception_frame_qword(frame, 11))
    console_write_register("r13".c_str(), exception_frame_qword(frame, 12))
    console_write_register("r14".c_str(), exception_frame_qword(frame, 13))
    console_write_register("r15".c_str(), exception_frame_qword(frame, 14))

    seq_terminate()

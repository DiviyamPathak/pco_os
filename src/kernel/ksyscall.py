from khal import get_active_scheduler
from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_ptr
from kconsole import console_write_u64
from ksched import scheduler_current_task
from ksched import scheduler_exit_current_task
from ksched import scheduler_runnable_count
from ksched import scheduler_yield_current_task
from ksupport import panic
from ktime import current_kernel_ticks


def syscall_write_number():
    return 1


def syscall_getpid_number():
    return 2


def syscall_clock_ticks_number():
    return 3


def syscall_yield_number():
    return 4


def syscall_exit_number():
    return 5


def active_scheduler_state():
    state_ptr = get_active_scheduler()
    if state_ptr == 0:
        panic("syscalls require active scheduler".c_str())
    return state_ptr


def syscall_dispatch(number: int, a0: int, a1: int, a2: int, a3: int, a4: int, a5: int):
    if number == syscall_write_number():
        console_write_ptr(a0)
        return 0

    if number == syscall_getpid_number():
        return scheduler_current_task(active_scheduler_state())

    if number == syscall_clock_ticks_number():
        return current_kernel_ticks()

    if number == syscall_yield_number():
        return scheduler_yield_current_task(active_scheduler_state())

    if number == syscall_exit_number():
        return scheduler_exit_current_task(active_scheduler_state(), a0)

    panic("unknown syscall number".c_str())


def sys_write(msg: cobj):
    console_write(msg)


def sys_write_u64(value: int):
    console_write_u64(value)


def sys_getpid():
    return syscall_dispatch(syscall_getpid_number(), 0, 0, 0, 0, 0, 0)


def sys_clock_ticks():
    return syscall_dispatch(syscall_clock_ticks_number(), 0, 0, 0, 0, 0, 0)


def sys_yield():
    return syscall_dispatch(syscall_yield_number(), 0, 0, 0, 0, 0, 0)


def sys_exit(code: int):
    return syscall_dispatch(syscall_exit_number(), code, 0, 0, 0, 0, 0)


def syscall_self_test():
    sys_write("syscall self-test begin\n".c_str())
    console_write_label_u64("sys.pid=".c_str(), sys_getpid())
    console_write_label_u64("sys.ticks=".c_str(), sys_clock_ticks())
    console_write_label_u64("sys.yield.to=".c_str(), sys_yield())
    console_write_label_u64("sys.pid.after_yield=".c_str(), sys_getpid())
    console_write_label_u64("sys.exit.next=".c_str(), sys_exit(42))
    console_write_label_u64("sys.runnable=".c_str(), scheduler_runnable_count(active_scheduler_state()))
    console_write_line("syscall self-test ok".c_str())

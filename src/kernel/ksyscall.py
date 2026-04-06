from khal import get_active_scheduler
from khal import invoke_syscall
from kconsole import console_put_byte
from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_ptr
from kconsole import console_write_u64
from ksched import scheduler_create_user_task
from ksched import scheduler_current_task
from ksched import scheduler_exit_current_task
from ksched import scheduler_runnable_count
from ksched import scheduler_task_mode
from ksched import scheduler_task_user_base
from ksched import scheduler_task_user_limit
from ksched import scheduler_waitpid
from ksched import scheduler_yield_current_task
from ksched import task_mode_user
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


def syscall_waitpid_number():
    return 6


def syscall_spawn_user_demo_number():
    return 7


def active_scheduler_state():
    state_ptr = get_active_scheduler()
    if state_ptr == 0:
        panic("syscalls require active scheduler".c_str())
    return state_ptr


def syscall_write_user_ptr(state_ptr: int, task_id: int, ptr: int):
    base = scheduler_task_user_base(state_ptr, task_id)
    limit = scheduler_task_user_limit(state_ptr, task_id)
    if base == 0 or limit <= base:
        return -1
    if ptr < base or ptr >= limit:
        return -1

    msg = Ptr[byte](ptr)
    length = 0
    current = ptr
    while current < limit:
        ch = msg[length]
        if ch == byte(0):
            return length
        console_put_byte(ch)
        length += 1
        current += 1
    return -1


def syscall_dispatch(number: int, a0: int, a1: int, a2: int, a3: int, a4: int, a5: int):
    state_ptr = active_scheduler_state()
    current_task = scheduler_current_task(state_ptr)

    if number == syscall_write_number():
        if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
            return syscall_write_user_ptr(state_ptr, current_task, a0)
        console_write_ptr(a0)
        return 0

    if number == syscall_getpid_number():
        return current_task

    if number == syscall_clock_ticks_number():
        return current_kernel_ticks()

    if number == syscall_yield_number():
        return scheduler_yield_current_task(state_ptr)

    if number == syscall_exit_number():
        if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
            console_write_line("user syscall exit".c_str())
        scheduler_exit_current_task(state_ptr, a0)
        return 0

    if number == syscall_waitpid_number():
        return scheduler_waitpid(state_ptr, a0)

    if number == syscall_spawn_user_demo_number():
        return scheduler_create_user_task(state_ptr, 100 + scheduler_runnable_count(state_ptr))

    panic("unknown syscall number".c_str())


def sys_write(msg: cobj):
    console_write(msg)


def sys_write_u64(value: int):
    console_write_u64(value)


def sys_getpid():
    return invoke_syscall(syscall_getpid_number(), 0, 0, 0, 0, 0)


def sys_clock_ticks():
    return invoke_syscall(syscall_clock_ticks_number(), 0, 0, 0, 0, 0)


def sys_yield():
    return invoke_syscall(syscall_yield_number(), 0, 0, 0, 0, 0)


def sys_exit(code: int):
    return invoke_syscall(syscall_exit_number(), code, 0, 0, 0, 0)


def sys_waitpid(task_id: int):
    return invoke_syscall(syscall_waitpid_number(), task_id, 0, 0, 0, 0)


def sys_spawn_user_demo():
    return invoke_syscall(syscall_spawn_user_demo_number(), 0, 0, 0, 0, 0)


@export
def syscall_entry(number: int, a0: int, a1: int, a2: int, a3: int, a4: int):
    return syscall_dispatch(number, a0, a1, a2, a3, a4, 0)


def syscall_self_test():
    sys_write("syscall self-test begin\n".c_str())
    console_write_label_u64("sys.pid=".c_str(), sys_getpid())
    console_write_label_u64("sys.ticks=".c_str(), sys_clock_ticks())
    console_write_label_u64("sys.runnable=".c_str(), scheduler_runnable_count(active_scheduler_state()))
    console_write_line("syscall self-test ok".c_str())

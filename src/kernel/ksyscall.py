from khal import get_active_scheduler
from khal import invoke_syscall
from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from ksched import scheduler_create_user_task
from ksched import scheduler_current_task
from ksched import scheduler_exit_current_task
from ksched import scheduler_runnable_count
from ksched import scheduler_set_task_fd_object
from ksched import scheduler_task_fd_object
from ksched import scheduler_task_mode
from ksched import scheduler_task_user_base
from ksched import scheduler_task_user_limit
from ksched import scheduler_vfs_state
from ksched import scheduler_waitpid
from ksched import scheduler_yield_current_task
from ksched import task_mode_user
from kvfs import vfs_close_descriptor
from kvfs import vfs_open_path
from kvfs import vfs_read_descriptor
from kvfs import vfs_write_descriptor
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


def syscall_close_number():
    return 8


def syscall_open_number():
    return 9


def syscall_read_number():
    return 10


def active_scheduler_state():
    state_ptr = get_active_scheduler()
    if state_ptr == 0:
        panic("syscalls require active scheduler".c_str())
    return state_ptr


def syscall_validate_user_buffer(state_ptr: int, task_id: int, ptr: int, length: int):
    base = scheduler_task_user_base(state_ptr, task_id)
    limit = scheduler_task_user_limit(state_ptr, task_id)
    if base == 0 or limit <= base:
        return False
    if length < 0:
        return False
    if ptr == 0 and length != 0:
        return False
    if ptr < base:
        return False
    if ptr + length < ptr or ptr + length > limit:
        return False
    return True


def syscall_write_user_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if not syscall_validate_user_buffer(state_ptr, task_id, ptr, length):
        return -1
    return vfs_write_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_write_kernel_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if length < 0:
        return -1
    if ptr == 0 and length != 0:
        return -1
    return vfs_write_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_alloc_task_fd(state_ptr: int, task_id: int, desc_id: int):
    fd = 3
    while fd >= 0:
        if scheduler_task_fd_object(state_ptr, task_id, fd) == 0:
            scheduler_set_task_fd_object(state_ptr, task_id, fd, desc_id)
            return fd
        fd -= 1
    return -1


def syscall_read_user_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if not syscall_validate_user_buffer(state_ptr, task_id, ptr, length):
        return -1
    return vfs_read_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_read_kernel_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if length < 0:
        return -1
    if ptr == 0 and length != 0:
        return -1
    return vfs_read_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_open_user_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, flags: int):
    desc_id = 0
    if not syscall_validate_user_buffer(state_ptr, task_id, path_ptr, path_len):
        return -1
    desc_id = vfs_open_path(scheduler_vfs_state(state_ptr), path_ptr, path_len, flags)
    if desc_id == 0:
        return -1
    fd = syscall_alloc_task_fd(state_ptr, task_id, desc_id)
    if fd < 0:
        vfs_close_descriptor(scheduler_vfs_state(state_ptr), desc_id)
        return -1
    return fd


def syscall_open_kernel_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, flags: int):
    desc_id = 0
    if path_ptr == 0 or path_len <= 0:
        return -1
    desc_id = vfs_open_path(scheduler_vfs_state(state_ptr), path_ptr, path_len, flags)
    if desc_id == 0:
        return -1
    fd = syscall_alloc_task_fd(state_ptr, task_id, desc_id)
    if fd < 0:
        vfs_close_descriptor(scheduler_vfs_state(state_ptr), desc_id)
        return -1
    return fd


def syscall_close_fd(state_ptr: int, task_id: int, fd: int):
    desc_id = scheduler_task_fd_object(state_ptr, task_id, fd)
    if desc_id == 0:
        return -1
    if vfs_close_descriptor(scheduler_vfs_state(state_ptr), desc_id) != 0:
        return -1
    scheduler_set_task_fd_object(state_ptr, task_id, fd, 0)
    return 0


def syscall_dispatch(number: int, a0: int, a1: int, a2: int, a3: int, a4: int, a5: int):
    state_ptr = active_scheduler_state()
    current_task = scheduler_current_task(state_ptr)

    if number == syscall_write_number():
        if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
            return syscall_write_user_buffer(state_ptr, current_task, a0, a1, a2)
        return syscall_write_kernel_buffer(state_ptr, current_task, a0, a1, a2)

    if number == syscall_open_number():
        if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
            return syscall_open_user_path(state_ptr, current_task, a0, a1, a2)
        return syscall_open_kernel_path(state_ptr, current_task, a0, a1, a2)

    if number == syscall_read_number():
        if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
            return syscall_read_user_buffer(state_ptr, current_task, a0, a1, a2)
        return syscall_read_kernel_buffer(state_ptr, current_task, a0, a1, a2)

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

    if number == syscall_close_number():
        return syscall_close_fd(state_ptr, current_task, a0)

    panic("unknown syscall number".c_str())


def sys_write(msg: cobj):
    console_write(msg)


def sys_write_u64(value: int):
    console_write_u64(value)


def sys_write_fd_ptr(fd: int, ptr: int, length: int):
    return invoke_syscall(syscall_write_number(), fd, ptr, length, 0, 0)


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


def sys_close(fd: int):
    return invoke_syscall(syscall_close_number(), fd, 0, 0, 0, 0)


def sys_open_ptr(path_ptr: int, path_len: int, flags: int):
    return invoke_syscall(syscall_open_number(), path_ptr, path_len, flags, 0, 0)


def sys_read(fd: int, ptr: int, length: int):
    return invoke_syscall(syscall_read_number(), fd, ptr, length, 0, 0)


@export
def syscall_entry(number: int, a0: int, a1: int, a2: int, a3: int, a4: int):
    return syscall_dispatch(number, a0, a1, a2, a3, a4, 0)


def syscall_self_test():
    sys_write("syscall self-test begin\n".c_str())
    console_write_label_u64("sys.pid=".c_str(), sys_getpid())
    console_write_label_u64("sys.ticks=".c_str(), sys_clock_ticks())
    console_write_label_u64("sys.runnable=".c_str(), scheduler_runnable_count(active_scheduler_state()))
    console_write_label_u64("sys.close.bad=".c_str(), sys_close(3))
    console_write_line("syscall self-test ok".c_str())

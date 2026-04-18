from khal import get_active_scheduler
from khal import invoke_syscall
from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from kelf import elf_validate_user_image
from ksched import scheduler_create_user_elf_task
from ksched import scheduler_current_task
from ksched import scheduler_exec_current_task
from ksched import scheduler_exit_current_task
from ksched import scheduler_runnable_count
from ksched import scheduler_set_task_fd_object
from ksched import scheduler_task_fd_object
from ksched import scheduler_task_mode
from ksched import scheduler_task_parent_pid
from ksched import scheduler_timer_interrupt
from ksched import scheduler_task_user_base
from ksched import scheduler_task_user_limit
from ksched import scheduler_vfs_state
from ksched import scheduler_waitpid
from ksched import scheduler_yield_current_task
from ksched import task_mode_user
from kvfs import vfs_close_descriptor
from kvfs import vfs_open_path
from kvfs import vfs_read_descriptor
from kvfs import vfs_readdir_descriptor
from kvfs import vfs_stat_descriptor
from kvfs import vfs_write_descriptor
from ksupport import alloc_bytes
from ksupport import load_byte_region
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_byte
from ksupport import store_qword_region
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


def syscall_fstat_number():
    return 11


def syscall_readdir_number():
    return 12


def syscall_spawn_exec_number():
    return 13


def syscall_exec_number():
    return 14


def syscall_getppid_number():
    return 15


def syscall_exec_max_args():
    return 8


def syscall_exec_max_env():
    return 8


def syscall_exec_max_string():
    return 64


def active_scheduler_state():
    state_ptr = get_active_scheduler()
    if state_ptr == 0:
        panic("syscalls require active scheduler".c_str())
    return state_ptr


def syscall_return_with_tick(state_ptr: int, allow_preempt: int, result: int):
    scheduler_timer_interrupt(state_ptr, allow_preempt)
    return result


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


def exec_vec_entry_ptr(vec_ptr: int, index: int):
    return vec_ptr + index * 16


def set_exec_vec_entry(vec_ptr: int, index: int, str_ptr: int, str_len: int):
    store_qword_region(exec_vec_entry_ptr(vec_ptr, index), 2, 0, str_ptr)
    store_qword_region(exec_vec_entry_ptr(vec_ptr, index), 2, 1, str_len)


def syscall_copy_kernel_cstring(ptr: int):
    length = 0
    dst = 0
    while length < syscall_exec_max_string():
        if load_byte_region(ptr, syscall_exec_max_string() + 1, length) == 0:
            dst = alloc_bytes(length + 1)
            copied = 0
            while copied < length:
                store_byte(dst + copied, load_byte_region(ptr, syscall_exec_max_string() + 1, copied))
                copied += 1
            store_byte(dst + length, 0)
            return dst, length
        length += 1
    return 0, 0


def syscall_copy_user_cstring(state_ptr: int, task_id: int, ptr: int):
    length = 0
    dst = 0
    if ptr == 0:
        return 0, 0
    while length < syscall_exec_max_string():
        if not syscall_validate_user_buffer(state_ptr, task_id, ptr, length + 1):
            return 0, 0
        if load_byte_region(ptr, length + 1, length) == 0:
            dst = alloc_bytes(length + 1)
            copied = 0
            while copied < length:
                store_byte(dst + copied, load_byte_region(ptr, length + 1, copied))
                copied += 1
            store_byte(dst + length, 0)
            return dst, length
        length += 1
    return 0, 0


def syscall_copy_kernel_exec_vector(array_ptr: int, max_count: int):
    count = 0
    str_ptr = 0
    str_len = 0
    vec_ptr = 0
    if array_ptr == 0:
        return 0, 0
    vec_ptr = alloc_bytes(max_count * 16)
    while count < max_count:
        entry_ptr = load_qword_region(array_ptr, max_count + 1, count)
        if entry_ptr == 0:
            return vec_ptr, count
        str_ptr, str_len = syscall_copy_kernel_cstring(entry_ptr)
        if str_ptr == 0:
            return 0, 0
        set_exec_vec_entry(vec_ptr, count, str_ptr, str_len)
        count += 1
    if load_qword_region(array_ptr, max_count + 1, max_count) != 0:
        return 0, 0
    return vec_ptr, count


def syscall_copy_user_exec_vector(state_ptr: int, task_id: int, array_ptr: int, max_count: int):
    count = 0
    entry_ptr = 0
    str_ptr = 0
    str_len = 0
    vec_ptr = 0
    if array_ptr == 0:
        return 0, 0
    if (array_ptr & 0x7) != 0:
        return 0, 0
    vec_ptr = alloc_bytes(max_count * 16)
    while count < max_count:
        if not syscall_validate_user_buffer(state_ptr, task_id, array_ptr + count * 8, 8):
            return 0, 0
        entry_ptr = load_qword_region(array_ptr, max_count + 1, count)
        if entry_ptr == 0:
            return vec_ptr, count
        str_ptr, str_len = syscall_copy_user_cstring(state_ptr, task_id, entry_ptr)
        if str_ptr == 0:
            return 0, 0
        set_exec_vec_entry(vec_ptr, count, str_ptr, str_len)
        count += 1
    if not syscall_validate_user_buffer(state_ptr, task_id, array_ptr + max_count * 8, 8):
        return 0, 0
    if load_qword_region(array_ptr, max_count + 1, max_count) != 0:
        return 0, 0
    return vec_ptr, count


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


def syscall_load_exec_image(vfs_state: int, path_ptr: int, path_len: int):
    desc_id = 0
    stat_buf = 0
    image_len = 0
    image_ptr = 0
    read_count = 0
    if path_ptr == 0 or path_len <= 0:
        return 0, 0

    desc_id = vfs_open_path(vfs_state, path_ptr, path_len, 0)
    if desc_id == 0:
        return 0, 0

    stat_buf = alloc_bytes(16)
    if vfs_stat_descriptor(vfs_state, desc_id, stat_buf) != 0:
        vfs_close_descriptor(vfs_state, desc_id)
        return 0, 0
    if load_qword_region(stat_buf, 2, 0) != 1:
        vfs_close_descriptor(vfs_state, desc_id)
        return 0, 0

    image_len = load_qword_region(stat_buf, 2, 1)
    if image_len <= 0 or image_len > 16384:
        vfs_close_descriptor(vfs_state, desc_id)
        return 0, 0

    image_ptr = alloc_bytes(image_len)
    read_count = vfs_read_descriptor(vfs_state, desc_id, image_ptr, image_len)
    vfs_close_descriptor(vfs_state, desc_id)
    if read_count != image_len:
        return 0, 0
    if not elf_validate_user_image(image_ptr, image_len):
        return 0, 0
    return image_ptr, image_len


def syscall_spawn_exec_kernel_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    image_ptr = 0
    image_len = 0
    argvec_ptr = 0
    arg_count = 0
    envvec_ptr = 0
    env_count = 0
    image_ptr, image_len = syscall_load_exec_image(scheduler_vfs_state(state_ptr), path_ptr, path_len)
    if image_ptr == 0:
        return -1
    argvec_ptr, arg_count = syscall_copy_kernel_exec_vector(argv_ptr, syscall_exec_max_args())
    if argv_ptr != 0 and argvec_ptr == 0:
        return -1
    envvec_ptr, env_count = syscall_copy_kernel_exec_vector(envp_ptr, syscall_exec_max_env())
    if envp_ptr != 0 and envvec_ptr == 0:
        return -1
    return scheduler_create_user_elf_task(state_ptr, 200 + scheduler_runnable_count(state_ptr), image_ptr, image_len, argvec_ptr, arg_count, envvec_ptr, env_count)


def syscall_spawn_exec_user_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    image_ptr = 0
    image_len = 0
    argvec_ptr = 0
    arg_count = 0
    envvec_ptr = 0
    env_count = 0
    if not syscall_validate_user_buffer(state_ptr, task_id, path_ptr, path_len):
        return -1
    argvec_ptr, arg_count = syscall_copy_user_exec_vector(state_ptr, task_id, argv_ptr, syscall_exec_max_args())
    if argv_ptr != 0 and argvec_ptr == 0:
        return -1
    envvec_ptr, env_count = syscall_copy_user_exec_vector(state_ptr, task_id, envp_ptr, syscall_exec_max_env())
    if envp_ptr != 0 and envvec_ptr == 0:
        return -1
    image_ptr, image_len = syscall_load_exec_image(scheduler_vfs_state(state_ptr), path_ptr, path_len)
    if image_ptr == 0:
        return -1
    return scheduler_create_user_elf_task(state_ptr, 200 + scheduler_runnable_count(state_ptr), image_ptr, image_len, argvec_ptr, arg_count, envvec_ptr, env_count)


def syscall_exec_kernel_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    image_ptr = 0
    image_len = 0
    argvec_ptr = 0
    arg_count = 0
    envvec_ptr = 0
    env_count = 0
    image_ptr, image_len = syscall_load_exec_image(scheduler_vfs_state(state_ptr), path_ptr, path_len)
    if image_ptr == 0:
        return -1
    argvec_ptr, arg_count = syscall_copy_kernel_exec_vector(argv_ptr, syscall_exec_max_args())
    if argv_ptr != 0 and argvec_ptr == 0:
        return -1
    envvec_ptr, env_count = syscall_copy_kernel_exec_vector(envp_ptr, syscall_exec_max_env())
    if envp_ptr != 0 and envvec_ptr == 0:
        return -1
    return scheduler_exec_current_task(state_ptr, image_ptr, image_len, argvec_ptr, arg_count, envvec_ptr, env_count)


def syscall_exec_user_path(state_ptr: int, task_id: int, path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    argvec_ptr = 0
    arg_count = 0
    envvec_ptr = 0
    env_count = 0
    image_ptr = 0
    image_len = 0
    if not syscall_validate_user_buffer(state_ptr, task_id, path_ptr, path_len):
        return -1
    argvec_ptr, arg_count = syscall_copy_user_exec_vector(state_ptr, task_id, argv_ptr, syscall_exec_max_args())
    if argv_ptr != 0 and argvec_ptr == 0:
        return -1
    envvec_ptr, env_count = syscall_copy_user_exec_vector(state_ptr, task_id, envp_ptr, syscall_exec_max_env())
    if envp_ptr != 0 and envvec_ptr == 0:
        return -1
    image_ptr, image_len = syscall_load_exec_image(scheduler_vfs_state(state_ptr), path_ptr, path_len)
    if image_ptr == 0:
        return -1
    return scheduler_exec_current_task(state_ptr, image_ptr, image_len, argvec_ptr, arg_count, envvec_ptr, env_count)


def syscall_fstat_user_buffer(state_ptr: int, task_id: int, fd: int, ptr: int):
    if not syscall_validate_user_buffer(state_ptr, task_id, ptr, 16):
        return -1
    return vfs_stat_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr)


def syscall_fstat_kernel_buffer(state_ptr: int, task_id: int, fd: int, ptr: int):
    if ptr == 0:
        return -1
    return vfs_stat_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr)


def syscall_readdir_user_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if not syscall_validate_user_buffer(state_ptr, task_id, ptr, length):
        return -1
    return vfs_readdir_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_readdir_kernel_buffer(state_ptr: int, task_id: int, fd: int, ptr: int, length: int):
    if length < 0:
        return -1
    if ptr == 0 and length != 0:
        return -1
    return vfs_readdir_descriptor(scheduler_vfs_state(state_ptr), scheduler_task_fd_object(state_ptr, task_id, fd), ptr, length)


def syscall_dispatch(number: int, a0: int, a1: int, a2: int, a3: int, a4: int, a5: int):
    state_ptr = active_scheduler_state()
    current_task = scheduler_current_task(state_ptr)
    user_mode = 0
    if scheduler_task_mode(state_ptr, current_task) == task_mode_user():
        user_mode = 1

    if number == syscall_write_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_write_user_buffer(state_ptr, current_task, a0, a1, a2))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_write_kernel_buffer(state_ptr, current_task, a0, a1, a2))

    if number == syscall_open_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_open_user_path(state_ptr, current_task, a0, a1, a2))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_open_kernel_path(state_ptr, current_task, a0, a1, a2))

    if number == syscall_read_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_read_user_buffer(state_ptr, current_task, a0, a1, a2))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_read_kernel_buffer(state_ptr, current_task, a0, a1, a2))

    if number == syscall_fstat_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_fstat_user_buffer(state_ptr, current_task, a0, a1))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_fstat_kernel_buffer(state_ptr, current_task, a0, a1))

    if number == syscall_readdir_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_readdir_user_buffer(state_ptr, current_task, a0, a1, a2))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_readdir_kernel_buffer(state_ptr, current_task, a0, a1, a2))

    if number == syscall_getpid_number():
        return syscall_return_with_tick(state_ptr, user_mode, current_task)

    if number == syscall_getppid_number():
        return syscall_return_with_tick(state_ptr, user_mode, scheduler_task_parent_pid(state_ptr, current_task))

    if number == syscall_clock_ticks_number():
        return syscall_return_with_tick(state_ptr, user_mode, current_kernel_ticks())

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
        return -1

    if number == syscall_spawn_exec_number():
        if user_mode != 0:
            return syscall_return_with_tick(state_ptr, user_mode, syscall_spawn_exec_user_path(state_ptr, current_task, a0, a1, a2, a3))
        return syscall_return_with_tick(state_ptr, user_mode, syscall_spawn_exec_kernel_path(state_ptr, current_task, a0, a1, a2, a3))

    if number == syscall_exec_number():
        if user_mode != 0:
            return syscall_exec_user_path(state_ptr, current_task, a0, a1, a2, a3)
        return syscall_exec_kernel_path(state_ptr, current_task, a0, a1, a2, a3)

    if number == syscall_close_number():
        return syscall_return_with_tick(state_ptr, user_mode, syscall_close_fd(state_ptr, current_task, a0))

    panic("unknown syscall number".c_str())


def sys_write(msg: cobj):
    console_write(msg)


def sys_write_u64(value: int):
    console_write_u64(value)


def sys_write_fd_ptr(fd: int, ptr: int, length: int):
    return invoke_syscall(syscall_write_number(), fd, ptr, length, 0, 0)


def sys_getpid():
    return invoke_syscall(syscall_getpid_number(), 0, 0, 0, 0, 0)


def sys_getppid():
    return invoke_syscall(syscall_getppid_number(), 0, 0, 0, 0, 0)


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


def sys_fstat(fd: int, ptr: int):
    return invoke_syscall(syscall_fstat_number(), fd, ptr, 0, 0, 0)


def sys_readdir(fd: int, ptr: int, length: int):
    return invoke_syscall(syscall_readdir_number(), fd, ptr, length, 0, 0)


def sys_spawn_exec_ptr(path_ptr: int, path_len: int):
    return invoke_syscall(syscall_spawn_exec_number(), path_ptr, path_len, 0, 0, 0)


def sys_spawn_execve_ptr(path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    return invoke_syscall(syscall_spawn_exec_number(), path_ptr, path_len, argv_ptr, envp_ptr, 0)


def sys_exec_ptr(path_ptr: int, path_len: int):
    return invoke_syscall(syscall_exec_number(), path_ptr, path_len, 0, 0, 0)


def sys_execve_ptr(path_ptr: int, path_len: int, argv_ptr: int, envp_ptr: int):
    return invoke_syscall(syscall_exec_number(), path_ptr, path_len, argv_ptr, envp_ptr, 0)


def sys_exec_cstring(path: cobj):
    length = sys_cstring_len(path)
    buf = alloc_bytes(length + 1)
    dst = Ptr[byte](buf)
    i = 0
    while i < length:
        dst[i] = path[i]
        i += 1
    dst[length] = byte(0)
    return sys_exec_ptr(buf, length)


def sys_cstring_len(msg: cobj):
    i = 0
    while msg[i] != byte(0):
        i += 1
    return i


def sys_spawn_exec_cstring(path: cobj):
    length = sys_cstring_len(path)
    buf = alloc_bytes(length + 1)
    dst = Ptr[byte](buf)
    i = 0
    while i < length:
        dst[i] = path[i]
        i += 1
    dst[length] = byte(0)
    return sys_spawn_exec_ptr(buf, length)


@export
def syscall_entry(number: int, a0: int, a1: int, a2: int, a3: int, a4: int):
    return syscall_dispatch(number, a0, a1, a2, a3, a4, 0)


def syscall_self_test():
    file_path = alloc_bytes(16)
    dir_path = alloc_bytes(4)
    buf = alloc_bytes(64)
    stat_buf = alloc_bytes(16)
    file_fd = 0
    dir_fd = 0
    stdin_count = 0

    store_byte(file_path + 0, 47)
    store_byte(file_path + 1, 104)
    store_byte(file_path + 2, 101)
    store_byte(file_path + 3, 108)
    store_byte(file_path + 4, 108)
    store_byte(file_path + 5, 111)
    store_byte(file_path + 6, 46)
    store_byte(file_path + 7, 116)
    store_byte(file_path + 8, 120)
    store_byte(file_path + 9, 116)
    store_byte(file_path + 10, 0)
    store_byte(dir_path + 0, 47)
    store_byte(dir_path + 1, 0)

    sys_write("syscall self-test begin\n".c_str())
    console_write_label_u64("sys.pid=".c_str(), sys_getpid())
    console_write_label_u64("sys.ppid=".c_str(), sys_getppid())
    console_write_label_u64("sys.ticks=".c_str(), sys_clock_ticks())
    console_write_label_u64("sys.runnable=".c_str(), scheduler_runnable_count(active_scheduler_state()))
    file_fd = sys_open_ptr(file_path, 10, 0)
    console_write_label_u64("sys.open.file=".c_str(), file_fd)
    console_write_label_u64("sys.read.file=".c_str(), sys_read(file_fd, buf, 64))
    if sys_fstat(file_fd, stat_buf) != 0:
        panic("syscall self-test fstat failed".c_str())
    console_write_label_u64("sys.fstat.kind=".c_str(), load_qword_region(stat_buf, 2, 0))
    console_write_label_u64("sys.fstat.size=".c_str(), load_qword_region(stat_buf, 2, 1))
    console_write_label_u64("sys.close.file=".c_str(), sys_close(file_fd))
    dir_fd = sys_open_ptr(dir_path, 1, 0)
    console_write_label_u64("sys.open.dir=".c_str(), dir_fd)
    dir_len = sys_readdir(dir_fd, buf, 64)
    console_write_label_u64("sys.readdir=".c_str(), dir_len)
    console_write("sys.readdir.sample=".c_str())
    if dir_len > 0:
        sys_write_fd_ptr(1, buf, dir_len)
    console_write("\n".c_str())
    console_write_label_u64("sys.close.dir=".c_str(), sys_close(dir_fd))
    stdin_count = sys_read(0, buf, 64)
    console_write_label_u64("sys.read.stdin=".c_str(), stdin_count)
    console_write_label_u64("sys.close.bad=".c_str(), sys_close(99))
    console_write_line("syscall self-test ok".c_str())

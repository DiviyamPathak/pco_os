from ksupport import alloc_bytes
from ksupport import load_byte
from ksupport import load_qword_region
from ksupport import store_byte
from ksyscall import sys_clock_ticks
from ksyscall import sys_close
from ksyscall import sys_fstat
from ksyscall import sys_open_ptr
from ksyscall import sys_read
from ksyscall import sys_readdir
from ksyscall import sys_spawn_exec_ptr
from ksyscall import sys_waitpid
from ksyscall import sys_write
from ksyscall import sys_write_fd_ptr
from ksyscall import sys_write_u64
from ksyscall import sys_yield


def shell_line_capacity():
    return 128


def shell_io_capacity():
    return 128


def shell_prompt():
    sys_write("pco> ".c_str())


def shell_cstring_len(msg: cobj):
    i = 0
    while msg[i] != byte(0):
        i += 1
    return i


def shell_buffer_equals(ptr: int, length: int, msg: cobj):
    src = Ptr[byte](ptr)
    msg_len = shell_cstring_len(msg)
    i = 0
    if length != msg_len:
        return False
    while i < msg_len:
        if src[i] != msg[i]:
            return False
        i += 1
    return True


def shell_buffer_startswith(ptr: int, length: int, msg: cobj):
    src = Ptr[byte](ptr)
    msg_len = shell_cstring_len(msg)
    i = 0
    if length < msg_len:
        return False
    while i < msg_len:
        if src[i] != msg[i]:
            return False
        i += 1
    return True


def shell_copy_cstring(dst_ptr: int, msg: cobj):
    dst = Ptr[byte](dst_ptr)
    i = 0
    while True:
        dst[i] = msg[i]
        if msg[i] == byte(0):
            return i
        i += 1


def shell_print_open_failed():
    sys_write("open failed\n".c_str())


def shell_print_help():
    sys_write("help              show commands\n".c_str())
    sys_write("pwd               print current path\n".c_str())
    sys_write("clear             clear the console\n".c_str())
    sys_write("ls                list root directory\n".c_str())
    sys_write("cat <path>        print a file\n".c_str())
    sys_write("stat <path>       print file metadata\n".c_str())
    sys_write("ticks             print kernel tick count\n".c_str())
    sys_write("spawn             run /bin/demo\n".c_str())
    sys_write("run <path>        exec a user program\n".c_str())


def shell_run_ls(root_path_ptr: int, io_buf: int):
    fd = sys_open_ptr(root_path_ptr, 1, 0)
    count = 0
    if fd < 0:
        shell_print_open_failed()
        return

    while True:
        count = sys_readdir(fd, io_buf, shell_io_capacity())
        if count <= 0:
            break
        sys_write_fd_ptr(1, io_buf, count)
        sys_write("\n".c_str())

    sys_close(fd)


def shell_run_cat(path_ptr: int, path_len: int, io_buf: int):
    fd = sys_open_ptr(path_ptr, path_len, 0)
    count = 0
    if fd < 0:
        shell_print_open_failed()
        return

    while True:
        count = sys_read(fd, io_buf, shell_io_capacity())
        if count <= 0:
            break
        sys_write_fd_ptr(1, io_buf, count)
    sys_close(fd)
    sys_write("\n".c_str())


def shell_run_stat(path_ptr: int, path_len: int, stat_buf: int):
    fd = sys_open_ptr(path_ptr, path_len, 0)
    if fd < 0:
        shell_print_open_failed()
        return

    if sys_fstat(fd, stat_buf) != 0:
        sys_write("stat failed\n".c_str())
        sys_close(fd)
        return

    sys_write("kind=".c_str())
    sys_write_u64(load_qword_region(stat_buf, 2, 0))
    sys_write(" size=".c_str())
    sys_write_u64(load_qword_region(stat_buf, 2, 1))
    sys_write("\n".c_str())
    sys_close(fd)


def shell_run_spawn():
    path = alloc_bytes(16)
    pid = 0
    status = 0
    store_byte(path + 0, 47)
    store_byte(path + 1, 98)
    store_byte(path + 2, 105)
    store_byte(path + 3, 110)
    store_byte(path + 4, 47)
    store_byte(path + 5, 100)
    store_byte(path + 6, 101)
    store_byte(path + 7, 109)
    store_byte(path + 8, 111)
    store_byte(path + 9, 0)
    pid = sys_spawn_exec_ptr(path, 9)
    sys_write("spawn pid=".c_str())
    sys_write_u64(pid)
    sys_write("\n".c_str())
    if pid < 0:
        return
    status = sys_waitpid(pid)
    sys_write("spawn status=".c_str())
    sys_write_u64(status)
    sys_write("\n".c_str())


def shell_run_exec(path_ptr: int, path_len: int):
    pid = 0
    status = 0

    pid = sys_spawn_exec_ptr(path_ptr, path_len)

    sys_write("run pid=".c_str())
    sys_write_u64(pid)
    sys_write("\n".c_str())
    if pid < 0:
        return
    status = sys_waitpid(pid)
    sys_write("run status=".c_str())
    sys_write_u64(status)
    sys_write("\n".c_str())


def shell_execute_line(line_ptr: int, line_len: int, root_path_ptr: int, io_buf: int, stat_buf: int):
    if line_len <= 0:
        return
    if shell_buffer_equals(line_ptr, line_len, "help".c_str()):
        shell_print_help()
        return
    if shell_buffer_equals(line_ptr, line_len, "pwd".c_str()):
        sys_write("/\n".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "clear".c_str()):
        sys_write("\x1b[2J\x1b[H".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "ls".c_str()):
        shell_run_ls(root_path_ptr, io_buf)
        return
    if shell_buffer_equals(line_ptr, line_len, "ticks".c_str()):
        sys_write("ticks=".c_str())
        sys_write_u64(sys_clock_ticks())
        sys_write("\n".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "spawn".c_str()):
        shell_run_spawn()
        return
    if line_len > 4 and shell_buffer_startswith(line_ptr, line_len, "run".c_str()) and load_byte(line_ptr + 3) == 32:
        shell_run_exec(line_ptr + 4, line_len - 4)
        return
    if line_len > 4 and shell_buffer_startswith(line_ptr, line_len, "cat".c_str()) and load_byte(line_ptr + 3) == 32:
        shell_run_cat(line_ptr + 4, line_len - 4, io_buf)
        return
    if line_len > 5 and shell_buffer_startswith(line_ptr, line_len, "stat".c_str()) and load_byte(line_ptr + 4) == 32:
        shell_run_stat(line_ptr + 5, line_len - 5, stat_buf)
        return
    sys_write("unknown command\n".c_str())


def shell_self_test():
    line_buf = alloc_bytes(shell_line_capacity())
    io_buf = alloc_bytes(shell_io_capacity())
    stat_buf = alloc_bytes(16)
    root_path = alloc_bytes(4)
    hello_path = alloc_bytes(16)
    hello_exec_path = alloc_bytes(16)

    store_byte(root_path + 0, 47)
    store_byte(root_path + 1, 0)
    store_byte(hello_path + 0, 47)
    store_byte(hello_path + 1, 104)
    store_byte(hello_path + 2, 101)
    store_byte(hello_path + 3, 108)
    store_byte(hello_path + 4, 108)
    store_byte(hello_path + 5, 111)
    store_byte(hello_path + 6, 46)
    store_byte(hello_path + 7, 116)
    store_byte(hello_path + 8, 120)
    store_byte(hello_path + 9, 116)
    store_byte(hello_path + 10, 0)
    store_byte(hello_exec_path + 0, 47)
    store_byte(hello_exec_path + 1, 98)
    store_byte(hello_exec_path + 2, 105)
    store_byte(hello_exec_path + 3, 110)
    store_byte(hello_exec_path + 4, 47)
    store_byte(hello_exec_path + 5, 104)
    store_byte(hello_exec_path + 6, 101)
    store_byte(hello_exec_path + 7, 108)
    store_byte(hello_exec_path + 8, 108)
    store_byte(hello_exec_path + 9, 111)
    store_byte(hello_exec_path + 10, 0)

    sys_write("shell self-test begin\n".c_str())
    shell_copy_cstring(line_buf, "help".c_str())
    shell_execute_line(line_buf, 4, root_path, io_buf, stat_buf)
    shell_copy_cstring(line_buf, "ls".c_str())
    shell_execute_line(line_buf, 2, root_path, io_buf, stat_buf)
    shell_copy_cstring(line_buf, "pwd".c_str())
    shell_execute_line(line_buf, 3, root_path, io_buf, stat_buf)
    shell_run_stat(hello_path, 10, stat_buf)
    shell_run_cat(hello_path, 10, io_buf)
    shell_run_spawn()
    shell_run_exec(hello_exec_path, 10)
    shell_copy_cstring(line_buf, "ticks".c_str())
    shell_execute_line(line_buf, 5, root_path, io_buf, stat_buf)
    sys_write("shell self-test ok\n".c_str())


def shell_run():
    line_buf = alloc_bytes(shell_line_capacity())
    read_buf = alloc_bytes(shell_io_capacity())
    io_buf = alloc_bytes(shell_io_capacity())
    stat_buf = alloc_bytes(16)
    root_path = alloc_bytes(4)
    line_len = 0
    read_count = 0
    read_index = 0
    ch = 0

    store_byte(root_path + 0, 47)
    store_byte(root_path + 1, 0)
    store_byte(line_buf + 0, 0)

    sys_write("shell ready\n".c_str())
    shell_prompt()
    while True:
        sys_yield()
        read_count = sys_read(0, read_buf, shell_io_capacity())
        read_index = 0
        while read_index < read_count:
            ch = load_byte(read_buf + read_index)
            read_index += 1

            if ch == 0:
                continue

            if ch == 8 or ch == 127:
                if line_len > 0:
                    line_len -= 1
                    store_byte(line_buf + line_len, 0)
                    sys_write("\b \b".c_str())
                continue

            if ch == 10:
                sys_write("\n".c_str())
                store_byte(line_buf + line_len, 0)
                shell_execute_line(line_buf, line_len, root_path, io_buf, stat_buf)
                line_len = 0
                store_byte(line_buf + 0, 0)
                shell_prompt()
                continue

            if ch < 32 or ch > 126:
                continue

            if line_len + 1 >= shell_line_capacity():
                continue

            store_byte(line_buf + line_len, ch)
            line_len += 1
            store_byte(line_buf + line_len, 0)
            sys_write_fd_ptr(1, read_buf + read_index - 1, 1)

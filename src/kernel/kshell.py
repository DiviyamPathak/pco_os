from ksupport import alloc_bytes
from ksupport import load_byte
from ksupport import load_qword_region
from ksupport import store_byte
from ksupport import store_qword_region
from ksyscall import sys_clock_ticks
from ksyscall import sys_close
from ksyscall import sys_fstat
from ksyscall import sys_getppid
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


def shell_path_capacity():
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


def shell_copy_buffer(dst_ptr: int, src_ptr: int, length: int):
    i = 0
    while i < length:
        store_byte(dst_ptr + i, load_byte(src_ptr + i))
        i += 1
    store_byte(dst_ptr + length, 0)


def shell_normalize_path(src_ptr: int, src_len: int, dst_ptr: int):
    src_index = 0
    dst_len = 0
    component_start = 0

    if src_ptr == 0 or src_len <= 0:
        return -1
    if load_byte(src_ptr + 0) != 47:
        return -1

    store_byte(dst_ptr + 0, 47)
    dst_len = 1
    src_index = 1

    while src_index < src_len:
        while src_index < src_len and load_byte(src_ptr + src_index) == 47:
            src_index += 1
        if src_index >= src_len:
            break

        component_start = src_index
        while src_index < src_len and load_byte(src_ptr + src_index) != 47:
            src_index += 1

        component_len = src_index - component_start
        if component_len == 1 and load_byte(src_ptr + component_start) == 46:
            continue
        if component_len == 2 and load_byte(src_ptr + component_start) == 46 and load_byte(src_ptr + component_start + 1) == 46:
            if dst_len > 1:
                dst_len -= 1
                while dst_len > 1 and load_byte(dst_ptr + dst_len - 1) != 47:
                    dst_len -= 1
            continue

        if dst_len > 1:
            store_byte(dst_ptr + dst_len, 47)
            dst_len += 1

        component_index = 0
        while component_index < component_len:
            store_byte(dst_ptr + dst_len, load_byte(src_ptr + component_start + component_index))
            dst_len += 1
            component_index += 1

    store_byte(dst_ptr + dst_len, 0)
    return dst_len


def shell_resolve_path(cwd_ptr: int, cwd_len: int, path_ptr: int, path_len: int, dst_ptr: int):
    copied = 0

    if path_len <= 0:
        return -1

    if load_byte(path_ptr + 0) == 47:
        shell_copy_buffer(dst_ptr, path_ptr, path_len)
        return path_len

    if cwd_len <= 0:
        return -1

    if cwd_len == 1 and load_byte(cwd_ptr + 0) == 47:
        store_byte(dst_ptr + 0, 47)
        copied = 0
        while copied < path_len:
            store_byte(dst_ptr + copied + 1, load_byte(path_ptr + copied))
            copied += 1
        store_byte(dst_ptr + path_len + 1, 0)
        return path_len + 1

    shell_copy_buffer(dst_ptr, cwd_ptr, cwd_len)
    store_byte(dst_ptr + cwd_len, 47)
    copied = 0
    while copied < path_len:
        store_byte(dst_ptr + cwd_len + 1 + copied, load_byte(path_ptr + copied))
        copied += 1
    store_byte(dst_ptr + cwd_len + 1 + path_len, 0)
    return cwd_len + 1 + path_len


def shell_print_open_failed():
    sys_write("open failed\n".c_str())


def shell_print_cd_failed():
    sys_write("cd failed\n".c_str())


def shell_print_help():
    sys_write("help              show commands\n".c_str())
    sys_write("pwd               print current path\n".c_str())
    sys_write("ppid              print parent pid\n".c_str())
    sys_write("clear             clear the console\n".c_str())
    sys_write("ls                list root directory\n".c_str())
    sys_write("cat <path>        print a file\n".c_str())
    sys_write("stat <path>       print file metadata\n".c_str())
    sys_write("ticks             print kernel tick count\n".c_str())
    sys_write("spawn             run /bin/demo\n".c_str())
    sys_write("run <path>        exec a user program\n".c_str())


def shell_run_ls(path_ptr: int, path_len: int, io_buf: int):
    fd = sys_open_ptr(path_ptr, path_len, 0)
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


def shell_run_cd(path_ptr: int, path_len: int, cwd_ptr: int, cwd_len_ptr: int, stat_buf: int):
    fd = sys_open_ptr(path_ptr, path_len, 0)
    if fd < 0:
        shell_print_cd_failed()
        return
    if sys_fstat(fd, stat_buf) != 0 or load_qword_region(stat_buf, 2, 0) != 2:
        shell_print_cd_failed()
        sys_close(fd)
        return
    shell_copy_buffer(cwd_ptr, path_ptr, path_len)
    store_qword_region(cwd_len_ptr, 1, 0, path_len)
    sys_close(fd)


def shell_execute_line(line_ptr: int, line_len: int, cwd_ptr: int, cwd_len_ptr: int, io_buf: int, stat_buf: int, path_buf: int):
    line = Ptr[byte](line_ptr)
    cwd_len = load_qword_region(cwd_len_ptr, 1, 0)
    resolved_len = 0
    if line_len <= 0:
        return
    if shell_buffer_equals(line_ptr, line_len, "help".c_str()):
        shell_print_help()
        return
    if shell_buffer_equals(line_ptr, line_len, "pwd".c_str()):
        sys_write_fd_ptr(1, cwd_ptr, cwd_len)
        sys_write("\n".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "ppid".c_str()):
        sys_write("ppid=".c_str())
        sys_write_u64(sys_getppid())
        sys_write("\n".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "clear".c_str()):
        sys_write("\x1b[2J\x1b[H".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "ls".c_str()):
        shell_run_ls(cwd_ptr, cwd_len, io_buf)
        return
    if shell_buffer_equals(line_ptr, line_len, "ticks".c_str()):
        sys_write("ticks=".c_str())
        sys_write_u64(sys_clock_ticks())
        sys_write("\n".c_str())
        return
    if shell_buffer_equals(line_ptr, line_len, "spawn".c_str()):
        shell_run_spawn()
        return
    if line_len > 3 and line[0] == byte(99) and line[1] == byte(100) and line[2] == byte(32):
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 3, line_len - 3, path_buf)
        if resolved_len <= 0:
            shell_print_cd_failed()
            return
        shell_run_cd(path_buf, resolved_len, cwd_ptr, cwd_len_ptr, stat_buf)
        return
    if line_len > 3 and line[0] == byte(108) and line[1] == byte(115) and line[2] == byte(32):
        if load_byte(line_ptr + 3) == 47:
            shell_run_ls(line_ptr + 3, line_len - 3, io_buf)
            return
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 3, line_len - 3, path_buf)
        if resolved_len <= 0:
            shell_print_open_failed()
            return
        shell_run_ls(path_buf, resolved_len, io_buf)
        return
    if line_len > 4 and shell_buffer_startswith(line_ptr, line_len, "run".c_str()) and load_byte(line_ptr + 3) == 32:
        if load_byte(line_ptr + 4) == 47:
            shell_run_exec(line_ptr + 4, line_len - 4)
            return
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 4, line_len - 4, path_buf)
        if resolved_len <= 0:
            shell_print_open_failed()
            return
        shell_run_exec(path_buf, resolved_len)
        return
    if line_len > 4 and shell_buffer_startswith(line_ptr, line_len, "cat".c_str()) and load_byte(line_ptr + 3) == 32:
        if load_byte(line_ptr + 4) == 47:
            shell_run_cat(line_ptr + 4, line_len - 4, io_buf)
            return
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 4, line_len - 4, path_buf)
        if resolved_len <= 0:
            shell_print_open_failed()
            return
        shell_run_cat(path_buf, resolved_len, io_buf)
        return
    if line_len > 5 and shell_buffer_startswith(line_ptr, line_len, "stat".c_str()) and load_byte(line_ptr + 4) == 32:
        if load_byte(line_ptr + 5) == 47:
            shell_run_stat(line_ptr + 5, line_len - 5, stat_buf)
            return
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 5, line_len - 5, path_buf)
        if resolved_len <= 0:
            shell_print_open_failed()
            return
        shell_run_stat(path_buf, resolved_len, stat_buf)
        return
    if line_len > 5 and shell_buffer_startswith(line_ptr, line_len, "stat".c_str()) and load_byte(line_ptr + 4) == 32:
        resolved_len = shell_resolve_path(cwd_ptr, cwd_len, line_ptr + 5, line_len - 5, path_buf)
        if resolved_len <= 0:
            shell_print_open_failed()
            return
        shell_run_stat(path_buf, resolved_len, stat_buf)
        return
    sys_write("unknown command\n".c_str())


def shell_self_test():
    line_buf = alloc_bytes(shell_line_capacity())
    io_buf = alloc_bytes(shell_io_capacity())
    stat_buf = alloc_bytes(16)
    path_buf = alloc_bytes(shell_path_capacity())
    cwd_buf = alloc_bytes(shell_path_capacity())
    cwd_len_ptr = alloc_bytes(8)
    bin_path = alloc_bytes(8)
    docs_dir_path = alloc_bytes(8)
    hello_path = alloc_bytes(16)
    docs_path = alloc_bytes(20)
    rwtest_exec_path = alloc_bytes(16)
    chain_exec_path = alloc_bytes(16)

    store_byte(cwd_buf + 0, 47)
    store_byte(cwd_buf + 1, 0)
    store_qword_region(cwd_len_ptr, 1, 0, 1)
    store_byte(bin_path + 0, 47)
    store_byte(bin_path + 1, 98)
    store_byte(bin_path + 2, 105)
    store_byte(bin_path + 3, 110)
    store_byte(bin_path + 4, 0)
    store_byte(docs_dir_path + 0, 47)
    store_byte(docs_dir_path + 1, 100)
    store_byte(docs_dir_path + 2, 111)
    store_byte(docs_dir_path + 3, 99)
    store_byte(docs_dir_path + 4, 115)
    store_byte(docs_dir_path + 5, 0)
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
    store_byte(docs_path + 0, 47)
    store_byte(docs_path + 1, 100)
    store_byte(docs_path + 2, 111)
    store_byte(docs_path + 3, 99)
    store_byte(docs_path + 4, 115)
    store_byte(docs_path + 5, 47)
    store_byte(docs_path + 6, 105)
    store_byte(docs_path + 7, 110)
    store_byte(docs_path + 8, 102)
    store_byte(docs_path + 9, 111)
    store_byte(docs_path + 10, 46)
    store_byte(docs_path + 11, 116)
    store_byte(docs_path + 12, 120)
    store_byte(docs_path + 13, 116)
    store_byte(docs_path + 14, 0)
    store_byte(rwtest_exec_path + 0, 47)
    store_byte(rwtest_exec_path + 1, 98)
    store_byte(rwtest_exec_path + 2, 105)
    store_byte(rwtest_exec_path + 3, 110)
    store_byte(rwtest_exec_path + 4, 47)
    store_byte(rwtest_exec_path + 5, 114)
    store_byte(rwtest_exec_path + 6, 119)
    store_byte(rwtest_exec_path + 7, 116)
    store_byte(rwtest_exec_path + 8, 101)
    store_byte(rwtest_exec_path + 9, 115)
    store_byte(rwtest_exec_path + 10, 116)
    store_byte(rwtest_exec_path + 11, 0)
    store_byte(chain_exec_path + 0, 47)
    store_byte(chain_exec_path + 1, 98)
    store_byte(chain_exec_path + 2, 105)
    store_byte(chain_exec_path + 3, 110)
    store_byte(chain_exec_path + 4, 47)
    store_byte(chain_exec_path + 5, 99)
    store_byte(chain_exec_path + 6, 104)
    store_byte(chain_exec_path + 7, 97)
    store_byte(chain_exec_path + 8, 105)
    store_byte(chain_exec_path + 9, 110)
    store_byte(chain_exec_path + 10, 0)

    sys_write("shell self-test begin\n".c_str())
    shell_copy_cstring(line_buf, "help".c_str())
    shell_execute_line(line_buf, 4, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
    shell_copy_cstring(line_buf, "ls".c_str())
    shell_execute_line(line_buf, 2, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
    shell_copy_cstring(line_buf, "pwd".c_str())
    shell_execute_line(line_buf, 3, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
    shell_copy_cstring(line_buf, "ppid".c_str())
    shell_execute_line(line_buf, 4, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
    shell_run_ls(bin_path, 4, io_buf)
    shell_run_ls(docs_dir_path, 5, io_buf)
    shell_run_stat(hello_path, 10, stat_buf)
    shell_run_cat(hello_path, 10, io_buf)
    shell_run_stat(docs_path, 14, stat_buf)
    shell_run_cat(docs_path, 14, io_buf)
    shell_run_spawn()
    shell_run_exec(rwtest_exec_path, 11)
    shell_run_exec(chain_exec_path, 10)
    shell_copy_cstring(line_buf, "ticks".c_str())
    shell_execute_line(line_buf, 5, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
    sys_write("shell self-test ok\n".c_str())


def shell_run():
    line_buf = alloc_bytes(shell_line_capacity())
    read_buf = alloc_bytes(shell_io_capacity())
    io_buf = alloc_bytes(shell_io_capacity())
    stat_buf = alloc_bytes(16)
    path_buf = alloc_bytes(shell_path_capacity())
    cwd_buf = alloc_bytes(shell_path_capacity())
    cwd_len_ptr = alloc_bytes(8)
    line_len = 0
    read_count = 0
    read_index = 0
    ch = 0

    store_byte(cwd_buf + 0, 47)
    store_byte(cwd_buf + 1, 0)
    store_qword_region(cwd_len_ptr, 1, 0, 1)
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
                shell_execute_line(line_buf, line_len, cwd_buf, cwd_len_ptr, io_buf, stat_buf, path_buf)
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

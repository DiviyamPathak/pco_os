from khal import arch_init
from khal import get_idt_base
from khal import get_idtr_base
from khal import serial_init
from kapic import arm_timer_masked
from kapic import dump_local_apic_summary
from kapic import dump_timer_summary
from kapic import init_local_apic
from kapic import probe_timer_progress
from kapic import probe_timer_interrupts
from kboot import dump_boot_info
from kconsole import console_write
from kconsole import console_write_hex
from kconsole import console_write_u64
from kconsole import init_console
from kconsole import print_msg
from kexceptions import handle_exception
from kexceptions import run_exception_test
from kidt import init_idt
from kshell import shell_run
from kshell import shell_self_test
from ksched import dump_scheduler_summary
from ksched import init_scheduler
from ksched import scheduler_enter_first_task
from ksched import scheduler_self_test
from ksyscall import sys_clock_ticks
from ksyscall import sys_exit
from ksyscall import sys_getpid
from ksyscall import sys_getppid
from ksyscall import sys_spawn_exec_ptr
from ksyscall import sys_spawn_execve_ptr
from ksyscall import sys_waitpid
from ksyscall import sys_write
from ksyscall import sys_write_u64
from ksyscall import sys_yield
from ksyscall import syscall_self_test
from ktime import wait_for_tick_edge
from ktime import start_kernel_tick_source
from ktime import timekeeping_self_test
from kmemory import dump_pmm_summary
from kmemory import dump_vmm_summary
from kmemory import init_pmm
from kmemory import init_vmm
from kmemory import pmm_self_test
from kmemory import vmm_self_test
from ksupport import alloc_bytes
from ksupport import panic
from ksupport import store_byte
from ksupport import store_qword_region
from kvfs import dump_vfs_summary
from kvfs import init_vfs
from kvfs import vfs_self_test


@export
def isr_dispatch(frame: int, vector: int, error_code: int):
    handle_exception(frame, vector, error_code)


def idle_task_main():
    while True:
        wait_for_tick_edge()
        sys_yield()


def worker_task_one():
    first_child = 0
    second_child = 0
    third_child = 0
    fourth_child = 0
    fifth_child = 0
    preempt_start = 0
    preempt_mid = 0
    demo_path = alloc_bytes(16)
    rwtest_path = alloc_bytes(16)
    chain_path = alloc_bytes(16)
    argv_path = alloc_bytes(16)
    hello_path = alloc_bytes(16)
    preempt_path = alloc_bytes(16)
    spawn_arg = alloc_bytes(16)
    spawn_env = alloc_bytes(16)
    spawn_argv = alloc_bytes(24)
    spawn_envp = alloc_bytes(16)

    store_byte(demo_path + 0, 47)
    store_byte(demo_path + 1, 98)
    store_byte(demo_path + 2, 105)
    store_byte(demo_path + 3, 110)
    store_byte(demo_path + 4, 47)
    store_byte(demo_path + 5, 100)
    store_byte(demo_path + 6, 101)
    store_byte(demo_path + 7, 109)
    store_byte(demo_path + 8, 111)
    store_byte(demo_path + 9, 0)
    store_byte(rwtest_path + 0, 47)
    store_byte(rwtest_path + 1, 98)
    store_byte(rwtest_path + 2, 105)
    store_byte(rwtest_path + 3, 110)
    store_byte(rwtest_path + 4, 47)
    store_byte(rwtest_path + 5, 114)
    store_byte(rwtest_path + 6, 119)
    store_byte(rwtest_path + 7, 116)
    store_byte(rwtest_path + 8, 101)
    store_byte(rwtest_path + 9, 115)
    store_byte(rwtest_path + 10, 116)
    store_byte(rwtest_path + 11, 0)
    store_byte(chain_path + 0, 47)
    store_byte(chain_path + 1, 98)
    store_byte(chain_path + 2, 105)
    store_byte(chain_path + 3, 110)
    store_byte(chain_path + 4, 47)
    store_byte(chain_path + 5, 99)
    store_byte(chain_path + 6, 104)
    store_byte(chain_path + 7, 97)
    store_byte(chain_path + 8, 105)
    store_byte(chain_path + 9, 110)
    store_byte(chain_path + 10, 0)
    store_byte(argv_path + 0, 47)
    store_byte(argv_path + 1, 98)
    store_byte(argv_path + 2, 105)
    store_byte(argv_path + 3, 110)
    store_byte(argv_path + 4, 47)
    store_byte(argv_path + 5, 97)
    store_byte(argv_path + 6, 114)
    store_byte(argv_path + 7, 103)
    store_byte(argv_path + 8, 118)
    store_byte(argv_path + 9, 0)
    store_byte(hello_path + 0, 47)
    store_byte(hello_path + 1, 98)
    store_byte(hello_path + 2, 105)
    store_byte(hello_path + 3, 110)
    store_byte(hello_path + 4, 47)
    store_byte(hello_path + 5, 104)
    store_byte(hello_path + 6, 101)
    store_byte(hello_path + 7, 108)
    store_byte(hello_path + 8, 108)
    store_byte(hello_path + 9, 111)
    store_byte(hello_path + 10, 0)
    store_byte(preempt_path + 0, 47)
    store_byte(preempt_path + 1, 98)
    store_byte(preempt_path + 2, 105)
    store_byte(preempt_path + 3, 110)
    store_byte(preempt_path + 4, 47)
    store_byte(preempt_path + 5, 112)
    store_byte(preempt_path + 6, 114)
    store_byte(preempt_path + 7, 101)
    store_byte(preempt_path + 8, 101)
    store_byte(preempt_path + 9, 109)
    store_byte(preempt_path + 10, 112)
    store_byte(preempt_path + 11, 116)
    store_byte(preempt_path + 12, 0)
    store_byte(spawn_arg + 0, 115)
    store_byte(spawn_arg + 1, 112)
    store_byte(spawn_arg + 2, 97)
    store_byte(spawn_arg + 3, 119)
    store_byte(spawn_arg + 4, 110)
    store_byte(spawn_arg + 5, 45)
    store_byte(spawn_arg + 6, 97)
    store_byte(spawn_arg + 7, 114)
    store_byte(spawn_arg + 8, 103)
    store_byte(spawn_arg + 9, 118)
    store_byte(spawn_arg + 10, 0)
    store_byte(spawn_env + 0, 77)
    store_byte(spawn_env + 1, 79)
    store_byte(spawn_env + 2, 68)
    store_byte(spawn_env + 3, 69)
    store_byte(spawn_env + 4, 61)
    store_byte(spawn_env + 5, 115)
    store_byte(spawn_env + 6, 112)
    store_byte(spawn_env + 7, 97)
    store_byte(spawn_env + 8, 119)
    store_byte(spawn_env + 9, 110)
    store_byte(spawn_env + 10, 0)
    store_qword_region(spawn_argv, 3, 0, argv_path)
    store_qword_region(spawn_argv, 3, 1, spawn_arg)
    store_qword_region(spawn_argv, 3, 2, 0)
    store_qword_region(spawn_envp, 2, 0, spawn_env)
    store_qword_region(spawn_envp, 2, 1, 0)

    sys_write("task1 start pid=".c_str())
    sys_write_u64(sys_getpid())
    sys_write(" ppid=".c_str())
    sys_write_u64(sys_getppid())
    sys_write("\n".c_str())

    first_child = sys_spawn_exec_ptr(demo_path, 9)
    sys_write("task1 spawned pid=".c_str())
    sys_write_u64(first_child)
    sys_write("\n".c_str())
    if first_child < 0:
        panic("exec demo spawn failed".c_str())

    status = sys_waitpid(first_child)
    sys_write("task1 waitpid=".c_str())
    sys_write_u64(first_child)
    sys_write(" status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(sys_clock_ticks())
    sys_write("\n".c_str())

    second_child = sys_spawn_exec_ptr(rwtest_path, 11)
    sys_write("task1 rwtest pid=".c_str())
    sys_write_u64(second_child)
    sys_write("\n".c_str())
    if second_child < 0:
        panic("exec rwtest spawn failed".c_str())

    if second_child != first_child:
        panic("scheduler slot reuse failed".c_str())

    status = sys_waitpid(second_child)
    sys_write("task1 rwtest waitpid=".c_str())
    sys_write_u64(second_child)
    sys_write(" status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(sys_clock_ticks())
    sys_write("\n".c_str())
    if status != 42:
        panic("rwtest status mismatch".c_str())

    third_child = sys_spawn_execve_ptr(argv_path, 9, spawn_argv, spawn_envp)
    sys_write("task1 argv pid=".c_str())
    sys_write_u64(third_child)
    sys_write("\n".c_str())
    if third_child < 0:
        panic("exec argv spawn failed".c_str())

    if third_child != second_child:
        panic("scheduler slot reuse failed".c_str())

    status = sys_waitpid(third_child)
    sys_write("task1 argv waitpid=".c_str())
    sys_write_u64(third_child)
    sys_write(" status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(sys_clock_ticks())
    sys_write("\n".c_str())
    if status != 33:
        panic("argv status mismatch".c_str())

    third_child = sys_spawn_exec_ptr(chain_path, 10)
    sys_write("task1 chain pid=".c_str())
    sys_write_u64(third_child)
    sys_write("\n".c_str())
    if third_child < 0:
        panic("exec chain spawn failed".c_str())

    if third_child != second_child:
        panic("scheduler slot reuse failed".c_str())

    status = sys_waitpid(third_child)
    sys_write("task1 chain waitpid=".c_str())
    sys_write_u64(third_child)
    sys_write(" status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(sys_clock_ticks())
    sys_write("\n".c_str())
    if status != 33:
        panic("chain exec status mismatch".c_str())

    preempt_start = sys_clock_ticks()
    fourth_child = sys_spawn_exec_ptr(preempt_path, 12)
    sys_write("task1 preempt slow pid=".c_str())
    sys_write_u64(fourth_child)
    sys_write("\n".c_str())
    if fourth_child < 0:
        panic("exec preempt spawn failed".c_str())

    fifth_child = sys_spawn_exec_ptr(hello_path, 10)
    sys_write("task1 preempt fast pid=".c_str())
    sys_write_u64(fifth_child)
    sys_write("\n".c_str())
    if fifth_child < 0:
        panic("exec hello spawn failed".c_str())
    if fifth_child == fourth_child:
        panic("scheduler failed to allocate second live child".c_str())

    status = sys_waitpid(fifth_child)
    preempt_mid = sys_clock_ticks()
    sys_write("task1 preempt fast status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(preempt_mid)
    sys_write("\n".c_str())
    if status != 7:
        panic("preempt fast status mismatch".c_str())
    if preempt_mid >= preempt_start + 4:
        panic("timer preemption did not advance fast child early".c_str())

    status = sys_waitpid(fourth_child)
    sys_write("task1 preempt slow status=".c_str())
    sys_write_u64(status)
    sys_write(" ticks=".c_str())
    sys_write_u64(sys_clock_ticks())
    sys_write("\n".c_str())
    if status != 55:
        panic("preempt slow status mismatch".c_str())

    shell_self_test()
    shell_run()


def worker_task_two():
    sys_write("task2 start pid=".c_str())
    sys_write_u64(sys_getpid())
    sys_write("\n".c_str())

    turn = 0
    while turn < 3:
        sys_write("task2 turn=".c_str())
        sys_write_u64(turn)
        sys_write(" ticks=".c_str())
        sys_write_u64(sys_clock_ticks())
        sys_write("\n".c_str())
        turn += 1
        sys_yield()

    sys_write("task2 exit=42\n".c_str())
    sys_exit(42)


@export
def task_bootstrap(task_id: int):
    if task_id == 0:
        idle_task_main()
        return
    if task_id == 1:
        worker_task_one()
        return
    if task_id == 2:
        worker_task_two()
        return

    console_write("unknown task id=".c_str())
    console_write_u64(task_id)
    console_write("\n".c_str())
    halt_forever()


@export
def task_returned(code: int):
    console_write("task returned code=".c_str())
    console_write_u64(code)
    console_write("\n".c_str())
    halt_forever()


def halt_forever():
    while True:
        wait_for_tick_edge()


@export
def kernel_main(boot_info_ptr: int):
    exception_test = 0
    lapic_timer_count = 10000000
    lapic_tick_reload = 1000000
    serial_init()
    init_console()
    arch_init()
    init_idt()
    console_write("Hello from Codon over serial!\n".c_str())
    console_write("idt base=".c_str())
    console_write_hex(get_idt_base())
    console_write(" idtr=".c_str())
    console_write_hex(get_idtr_base())
    console_write("\n".c_str())
    console_write("boot marker: ".c_str())
    console_write_hex(0xC0D0)
    console_write(" build=".c_str())
    console_write_u64(1)
    console_write("\n".c_str())
    dump_boot_info(boot_info_ptr)
    vfs_state = init_vfs(boot_info_ptr)
    dump_vfs_summary(vfs_state)
    vfs_self_test(vfs_state)
    pmm_state = init_pmm(boot_info_ptr)
    dump_pmm_summary(pmm_state)
    pmm_self_test(pmm_state)
    vmm_state = init_vmm(pmm_state, boot_info_ptr)
    dump_vmm_summary(vmm_state)
    vmm_self_test(vmm_state, pmm_state, boot_info_ptr)
    print_msg("PCO/OS console online".c_str(), 0, 0x0A)
    run_exception_test(exception_test)
    init_local_apic()
    dump_local_apic_summary()
    arm_timer_masked(lapic_timer_count)
    dump_timer_summary()
    probe_timer_progress()
    probe_timer_interrupts(lapic_tick_reload, 3)
    start_kernel_tick_source(lapic_tick_reload)
    timekeeping_self_test(5)
    scheduler_state = init_scheduler(pmm_state, vmm_state, vfs_state)
    dump_scheduler_summary(scheduler_state)
    syscall_self_test()
    dump_scheduler_summary(scheduler_state)
    scheduler_self_test(scheduler_state, 5)
    scheduler_enter_first_task(scheduler_state)

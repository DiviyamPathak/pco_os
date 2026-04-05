from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from khal import set_active_scheduler
from ksupport import alloc_bytes
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_qword_region
from ktime import current_kernel_ticks
from ktime import wait_for_tick_edge


def task_slot_id():
    return 0


def task_slot_state():
    return 1


def task_slot_runtime_ticks():
    return 2


def task_slot_switches():
    return 3


def task_slot_name_tag():
    return 4


def task_slot_wait_ticks():
    return 5


def task_slot_exit_code():
    return 6


def task_slot_limit():
    return 7


def task_state_empty():
    return 0


def task_state_runnable():
    return 1


def task_state_waiting():
    return 2


def task_state_exited():
    return 3


def max_tasks():
    return 4


def ready_queue_capacity():
    return 8


def sched_slot_task_count():
    return 0


def sched_slot_current_task():
    return 1


def sched_slot_idle_task():
    return 2


def sched_slot_last_tick():
    return 3


def sched_slot_last_report():
    return 4


def sched_slot_total_ticks():
    return 5


def sched_slot_idle_ticks():
    return 6


def sched_slot_switch_count():
    return 7


def sched_slot_task_table_ptr():
    return 8


def sched_slot_ready_queue_ptr():
    return 9


def sched_slot_ready_head():
    return 10


def sched_slot_ready_tail():
    return 11


def sched_slot_limit():
    return 12


def scheduler_state_qword(state_ptr: int, slot: int):
    return load_qword_region(state_ptr, sched_slot_limit(), slot)


def set_scheduler_state_qword(state_ptr: int, slot: int, value: int):
    store_qword_region(state_ptr, sched_slot_limit(), slot, value)


def scheduler_task_entry_ptr(task_table_ptr: int, task_id: int):
    if task_id < 0 or task_id >= max_tasks():
        panic("scheduler task id out of range".c_str())
    return task_table_ptr + task_id * task_slot_limit() * 8


def scheduler_task_qword(task_table_ptr: int, task_id: int, slot: int):
    return load_qword_region(scheduler_task_entry_ptr(task_table_ptr, task_id), task_slot_limit(), slot)


def set_scheduler_task_qword(task_table_ptr: int, task_id: int, slot: int, value: int):
    store_qword_region(scheduler_task_entry_ptr(task_table_ptr, task_id), task_slot_limit(), slot, value)


def ready_queue_qword(queue_ptr: int, slot: int):
    return load_qword_region(queue_ptr, ready_queue_capacity(), slot)


def set_ready_queue_qword(queue_ptr: int, slot: int, value: int):
    store_qword_region(queue_ptr, ready_queue_capacity(), slot, value)


def scheduler_task_count(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_task_count())


def scheduler_current_task(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_current_task())


def scheduler_idle_task(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_idle_task())


def scheduler_total_ticks(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_total_ticks())


def scheduler_idle_ticks(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_idle_ticks())


def scheduler_switch_count(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_switch_count())


def scheduler_task_table_ptr(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_task_table_ptr())


def scheduler_ready_queue_ptr(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_ready_queue_ptr())


def scheduler_ready_size(state_ptr: int):
    head = scheduler_state_qword(state_ptr, sched_slot_ready_head())
    tail = scheduler_state_qword(state_ptr, sched_slot_ready_tail())
    return tail - head


def scheduler_set_task(task_table_ptr: int, task_id: int, state: int, name_tag: int):
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_id(), task_id)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_state(), state)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_runtime_ticks(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_switches(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_name_tag(), name_tag)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_wait_ticks(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_exit_code(), 0)


def scheduler_enqueue_task(state_ptr: int, task_id: int):
    if task_id < 0 or task_id >= max_tasks():
        panic("scheduler enqueue task id out of range".c_str())

    size = scheduler_ready_size(state_ptr)
    if size >= ready_queue_capacity():
        panic("scheduler ready queue full".c_str())

    queue_ptr = scheduler_ready_queue_ptr(state_ptr)
    tail = scheduler_state_qword(state_ptr, sched_slot_ready_tail())
    set_ready_queue_qword(queue_ptr, tail % ready_queue_capacity(), task_id)
    set_scheduler_state_qword(state_ptr, sched_slot_ready_tail(), tail + 1)


def scheduler_dequeue_task(state_ptr: int):
    if scheduler_ready_size(state_ptr) == 0:
        return scheduler_idle_task(state_ptr)

    queue_ptr = scheduler_ready_queue_ptr(state_ptr)
    head = scheduler_state_qword(state_ptr, sched_slot_ready_head())
    task_id = ready_queue_qword(queue_ptr, head % ready_queue_capacity())
    set_scheduler_state_qword(state_ptr, sched_slot_ready_head(), head + 1)
    return task_id


def scheduler_task_state(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_state())


def scheduler_set_task_state(state_ptr: int, task_id: int, state: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_state(), state)


def scheduler_task_runtime_ticks(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_runtime_ticks())


def scheduler_task_switches(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_switches())


def scheduler_task_name_tag(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_name_tag())


def scheduler_task_exit_code(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_exit_code())


def scheduler_add_runtime_ticks(state_ptr: int, task_id: int, delta: int):
    table_ptr = scheduler_task_table_ptr(state_ptr)
    current = scheduler_task_qword(table_ptr, task_id, task_slot_runtime_ticks())
    set_scheduler_task_qword(table_ptr, task_id, task_slot_runtime_ticks(), current + delta)


def scheduler_record_switch(state_ptr: int, task_id: int):
    table_ptr = scheduler_task_table_ptr(state_ptr)
    current = scheduler_task_qword(table_ptr, task_id, task_slot_switches())
    set_scheduler_task_qword(table_ptr, task_id, task_slot_switches(), current + 1)


def scheduler_init_bootstrap_tasks(state_ptr: int):
    task_table_ptr = scheduler_task_table_ptr(state_ptr)
    scheduler_set_task(task_table_ptr, 0, task_state_runnable(), 0)
    scheduler_set_task(task_table_ptr, 1, task_state_runnable(), 1)
    scheduler_set_task(task_table_ptr, 2, task_state_runnable(), 2)

    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), 3)
    set_scheduler_state_qword(state_ptr, sched_slot_current_task(), 1)
    set_scheduler_state_qword(state_ptr, sched_slot_idle_task(), 0)

    scheduler_enqueue_task(state_ptr, 2)
    scheduler_enqueue_task(state_ptr, 0)
    scheduler_record_switch(state_ptr, 1)


def init_scheduler():
    state_ptr = alloc_bytes(sched_slot_limit() * 8)
    task_table_ptr = alloc_bytes(max_tasks() * task_slot_limit() * 8)
    ready_queue_ptr = alloc_bytes(ready_queue_capacity() * 8)
    now = current_kernel_ticks()

    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_current_task(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_idle_task(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_last_tick(), now)
    set_scheduler_state_qword(state_ptr, sched_slot_last_report(), now)
    set_scheduler_state_qword(state_ptr, sched_slot_total_ticks(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_idle_ticks(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_switch_count(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_task_table_ptr(), task_table_ptr)
    set_scheduler_state_qword(state_ptr, sched_slot_ready_queue_ptr(), ready_queue_ptr)
    set_scheduler_state_qword(state_ptr, sched_slot_ready_head(), 0)
    set_scheduler_state_qword(state_ptr, sched_slot_ready_tail(), 0)

    scheduler_init_bootstrap_tasks(state_ptr)
    set_active_scheduler(state_ptr)
    return state_ptr


def scheduler_pick_next_task(state_ptr: int):
    current_task = scheduler_current_task(state_ptr)
    if current_task != scheduler_idle_task(state_ptr):
        if scheduler_task_state(state_ptr, current_task) == task_state_runnable():
            scheduler_enqueue_task(state_ptr, current_task)

    attempts = scheduler_ready_size(state_ptr) + 1
    next_task = scheduler_idle_task(state_ptr)
    while attempts > 0:
        candidate = scheduler_dequeue_task(state_ptr)
        if candidate == scheduler_idle_task(state_ptr):
            attempts -= 1
            continue
        if scheduler_task_state(state_ptr, candidate) == task_state_runnable():
            next_task = candidate
            break
        attempts -= 1

    set_scheduler_state_qword(state_ptr, sched_slot_current_task(), next_task)
    set_scheduler_state_qword(state_ptr, sched_slot_switch_count(), scheduler_switch_count(state_ptr) + 1)
    scheduler_record_switch(state_ptr, next_task)
    return next_task


def scheduler_yield_current_task(state_ptr: int):
    return scheduler_pick_next_task(state_ptr)


def scheduler_exit_current_task(state_ptr: int, exit_code: int):
    current_task = scheduler_current_task(state_ptr)
    if current_task == scheduler_idle_task(state_ptr):
        panic("cannot exit idle task".c_str())
    table_ptr = scheduler_task_table_ptr(state_ptr)
    set_scheduler_task_qword(table_ptr, current_task, task_slot_state(), task_state_exited())
    set_scheduler_task_qword(table_ptr, current_task, task_slot_exit_code(), exit_code)
    return scheduler_pick_next_task(state_ptr)


def scheduler_runnable_count(state_ptr: int):
    task_id = 0
    runnable = 0
    while task_id < scheduler_task_count(state_ptr):
        if scheduler_task_state(state_ptr, task_id) == task_state_runnable():
            runnable += 1
        task_id += 1
    return runnable


def scheduler_account_tick(state_ptr: int, now: int):
    last_tick = scheduler_state_qword(state_ptr, sched_slot_last_tick())
    if now <= last_tick:
        return 0

    delta = now - last_tick
    current_task = scheduler_current_task(state_ptr)

    set_scheduler_state_qword(state_ptr, sched_slot_last_tick(), now)
    set_scheduler_state_qword(state_ptr, sched_slot_total_ticks(), scheduler_total_ticks(state_ptr) + delta)
    scheduler_add_runtime_ticks(state_ptr, current_task, delta)
    if current_task == scheduler_idle_task(state_ptr):
        set_scheduler_state_qword(state_ptr, sched_slot_idle_ticks(), scheduler_idle_ticks(state_ptr) + delta)
    return delta


def dump_scheduler_task_summary(state_ptr: int, task_id: int):
    console_write("sched.task[".c_str())
    console_write_u64(task_id)
    console_write("] tag=".c_str())
    console_write_u64(scheduler_task_name_tag(state_ptr, task_id))
    console_write(" runtime=".c_str())
    console_write_u64(scheduler_task_runtime_ticks(state_ptr, task_id))
    console_write(" switches=".c_str())
    console_write_u64(scheduler_task_switches(state_ptr, task_id))
    console_write(" state=".c_str())
    console_write_u64(scheduler_task_state(state_ptr, task_id))
    console_write(" exit=".c_str())
    console_write_u64(scheduler_task_exit_code(state_ptr, task_id))
    console_write("\n".c_str())


def dump_scheduler_summary(state_ptr: int):
    console_write_label_u64("sched.tasks=".c_str(), scheduler_task_count(state_ptr))
    console_write_label_u64("sched.runnable=".c_str(), scheduler_runnable_count(state_ptr))
    console_write_label_u64("sched.current=".c_str(), scheduler_current_task(state_ptr))
    console_write_label_u64("sched.idle=".c_str(), scheduler_idle_task(state_ptr))
    console_write_label_u64("sched.ready=".c_str(), scheduler_ready_size(state_ptr))
    console_write_label_u64("sched.ticks=".c_str(), scheduler_total_ticks(state_ptr))
    console_write_label_u64("sched.idle_ticks=".c_str(), scheduler_idle_ticks(state_ptr))
    console_write_label_u64("sched.switches=".c_str(), scheduler_switch_count(state_ptr))

    task_id = 0
    while task_id < scheduler_task_count(state_ptr):
        dump_scheduler_task_summary(state_ptr, task_id)
        task_id += 1


def scheduler_self_test(state_ptr: int, delta: int):
    if delta <= 0:
        panic("scheduler self-test requires ticks".c_str())

    start = scheduler_total_ticks(state_ptr)
    start_switches = scheduler_switch_count(state_ptr)
    observed = 0
    while observed < delta:
        now = wait_for_tick_edge()
        observed += scheduler_account_tick(state_ptr, now)
        scheduler_pick_next_task(state_ptr)

    end = scheduler_total_ticks(state_ptr)
    if end < start + delta:
        panic("scheduler tick accounting failed".c_str())
    if scheduler_switch_count(state_ptr) <= start_switches:
        panic("scheduler made no task decisions".c_str())

    console_write("sched.self_test.start=".c_str())
    console_write_u64(start)
    console_write("\n".c_str())
    console_write("sched.self_test.end=".c_str())
    console_write_u64(end)
    console_write("\n".c_str())
    console_write("sched.self_test.switches=".c_str())
    console_write_u64(scheduler_switch_count(state_ptr) - start_switches)
    console_write("\n".c_str())
    console_write_line("scheduler self-test ok".c_str())


def scheduler_idle_loop(state_ptr: int):
    report_every = 100

    while True:
        now = wait_for_tick_edge()
        delta = scheduler_account_tick(state_ptr, now)
        if delta == 0:
            continue

        scheduler_pick_next_task(state_ptr)

        last_report = scheduler_state_qword(state_ptr, sched_slot_last_report())
        if now - last_report >= report_every:
            set_scheduler_state_qword(state_ptr, sched_slot_last_report(), now)
            dump_scheduler_summary(state_ptr)

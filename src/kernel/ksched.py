from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from khal import context_switch
from khal import load_cr3
from khal import restore_task_context
from khal import set_active_scheduler
from khal import set_tss_rsp0
from khal import task_trampoline_addr
from khal import user_demo_entry_addr
from khal import user_task_trampoline_addr
from kmemory import copy_page
from kmemory import pmm_alloc_page
from kmemory import vmm_clone_kernel_address_space
from kmemory import vmm_map_page_root
from kmemory import vmm_state_qword
from kmemory import vmm_unmap_page_root
from kmemory import zero_page
from ksupport import align_down
from ksupport import alloc_bytes
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_qword_region
from ktime import current_kernel_ticks
from ktime import wait_for_tick_edge


def context_slot_rsp():
    return 0


def context_slot_rbx():
    return 1


def context_slot_rbp():
    return 2


def context_slot_r12():
    return 3


def context_slot_r13():
    return 4


def context_slot_r14():
    return 5


def context_slot_r15():
    return 6


def context_slot_limit():
    return 7


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


def task_slot_context_ptr():
    return 7


def task_slot_stack_base():
    return 8


def task_slot_mode():
    return 9


def task_slot_cr3():
    return 10


def task_slot_user_base():
    return 11


def task_slot_user_limit():
    return 12


def task_slot_limit():
    return 13


def task_state_empty():
    return 0


def task_state_runnable():
    return 1


def task_state_waiting():
    return 2


def task_state_exited():
    return 3


def task_mode_kernel():
    return 0


def task_mode_user():
    return 1


def max_tasks():
    return 8


def ready_queue_capacity():
    return 16


def task_stack_size():
    return 4096


def user_task_region_base(task_id: int):
    return 0x20000000 + task_id * 0x200000


def user_task_code_virt(task_id: int):
    return user_task_region_base(task_id)


def user_task_stack_virt(task_id: int):
    return user_task_region_base(task_id) + 0x1000


def user_task_data_virt(task_id: int):
    return user_task_region_base(task_id) + 0x2000


def user_task_stack_top(task_id: int):
    return user_task_region_base(task_id) + 0x2000


def task_kernel_rsp0_top(stack_base: int):
    return align_down(stack_base + task_stack_size(), 16)


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


def sched_slot_pmm_state():
    return 12


def sched_slot_vmm_state():
    return 13


def sched_slot_limit():
    return 14


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


def task_context_qword(ctx_ptr: int, slot: int):
    return load_qword_region(ctx_ptr, context_slot_limit(), slot)


def set_task_context_qword(ctx_ptr: int, slot: int, value: int):
    store_qword_region(ctx_ptr, context_slot_limit(), slot, value)


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


def scheduler_task_state(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_state())


def scheduler_task_runtime_ticks(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_runtime_ticks())


def scheduler_task_switches(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_switches())


def scheduler_task_name_tag(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_name_tag())


def scheduler_task_wait_ticks(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_wait_ticks())


def scheduler_task_exit_code(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_exit_code())


def scheduler_task_context_ptr(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_context_ptr())


def scheduler_task_stack_base(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_stack_base())


def scheduler_task_mode(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_mode())


def scheduler_task_cr3(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_cr3())


def scheduler_task_user_base(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_user_base())


def scheduler_task_user_limit(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_user_limit())


def scheduler_pmm_state(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_pmm_state())


def scheduler_vmm_state(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_vmm_state())


def scheduler_set_task_state(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_state(), value)


def scheduler_set_task_wait_ticks(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_wait_ticks(), value)


def scheduler_set_task_exit_code(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_exit_code(), value)


def scheduler_set_task(task_table_ptr: int, task_id: int, state: int, name_tag: int, ctx_ptr: int, stack_base: int, mode: int, cr3: int, user_base: int, user_limit: int):
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_id(), task_id)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_state(), state)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_runtime_ticks(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_switches(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_name_tag(), name_tag)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_wait_ticks(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_exit_code(), 0)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_context_ptr(), ctx_ptr)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_stack_base(), stack_base)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_mode(), mode)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_cr3(), cr3)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_user_base(), user_base)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_user_limit(), user_limit)


def scheduler_prepare_kernel_task_context(task_id: int):
    ctx_ptr = alloc_bytes(context_slot_limit() * 8)
    stack_base = alloc_bytes(task_stack_size())
    stack_top = align_down(stack_base + task_stack_size(), 16)
    initial_rsp = stack_top - 8

    store_qword_region(initial_rsp, 1, 0, task_trampoline_addr())
    set_task_context_qword(ctx_ptr, context_slot_rsp(), initial_rsp)
    set_task_context_qword(ctx_ptr, context_slot_rbx(), 0)
    set_task_context_qword(ctx_ptr, context_slot_rbp(), 0)
    set_task_context_qword(ctx_ptr, context_slot_r12(), task_id)
    set_task_context_qword(ctx_ptr, context_slot_r13(), 0)
    set_task_context_qword(ctx_ptr, context_slot_r14(), 0)
    set_task_context_qword(ctx_ptr, context_slot_r15(), 0)
    return ctx_ptr, stack_base


def scheduler_prepare_user_task_context(task_id: int, user_rip: int, user_rsp: int):
    ctx_ptr = alloc_bytes(context_slot_limit() * 8)
    stack_base = alloc_bytes(task_stack_size())
    stack_top = align_down(stack_base + task_stack_size(), 16)
    initial_rsp = stack_top - 8

    store_qword_region(initial_rsp, 1, 0, user_task_trampoline_addr())
    set_task_context_qword(ctx_ptr, context_slot_rsp(), initial_rsp)
    set_task_context_qword(ctx_ptr, context_slot_rbx(), 0)
    set_task_context_qword(ctx_ptr, context_slot_rbp(), 0)
    set_task_context_qword(ctx_ptr, context_slot_r12(), user_rip)
    set_task_context_qword(ctx_ptr, context_slot_r13(), user_rsp)
    set_task_context_qword(ctx_ptr, context_slot_r14(), user_task_data_virt(task_id))
    set_task_context_qword(ctx_ptr, context_slot_r15(), 0)
    return ctx_ptr, stack_base


def scheduler_write_cstring(dst_ptr: int, offset: int, msg: cobj):
    dst = Ptr[byte](dst_ptr + offset)
    i = 0
    while True:
        ch = msg[i]
        dst[i] = ch
        if ch == byte(0):
            return
        i += 1


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


def scheduler_add_runtime_ticks(state_ptr: int, task_id: int, delta: int):
    table_ptr = scheduler_task_table_ptr(state_ptr)
    current = scheduler_task_qword(table_ptr, task_id, task_slot_runtime_ticks())
    set_scheduler_task_qword(table_ptr, task_id, task_slot_runtime_ticks(), current + delta)


def scheduler_record_switch(state_ptr: int, task_id: int):
    table_ptr = scheduler_task_table_ptr(state_ptr)
    current = scheduler_task_qword(table_ptr, task_id, task_slot_switches())
    set_scheduler_task_qword(table_ptr, task_id, task_slot_switches(), current + 1)


def scheduler_find_free_task_id(state_ptr: int):
    task_id = scheduler_task_count(state_ptr)
    if task_id >= max_tasks():
        panic("scheduler task table full".c_str())
    return task_id


def scheduler_create_user_task(state_ptr: int, name_tag: int):
    task_id = scheduler_find_free_task_id(state_ptr)
    task_table_ptr = scheduler_task_table_ptr(state_ptr)
    pmm_state = scheduler_pmm_state(state_ptr)
    vmm_state = scheduler_vmm_state(state_ptr)
    user_cr3 = vmm_clone_kernel_address_space(vmm_state, pmm_state)
    code_src_phys = align_down(user_demo_entry_addr(), 4096)
    code_phys = pmm_alloc_page(pmm_state)
    data_phys = pmm_alloc_page(pmm_state)
    stack_phys = pmm_alloc_page(pmm_state)
    user_base = user_task_region_base(task_id)
    user_limit = user_base + 0x3000

    if code_phys == 0 or data_phys == 0 or stack_phys == 0:
        panic("scheduler user task alloc failed".c_str())

    copy_page(code_src_phys, code_phys)
    zero_page(data_phys)
    scheduler_write_cstring(data_phys, 0, "user task start\n".c_str())
    scheduler_write_cstring(data_phys, 32, "user task yield\n".c_str())
    scheduler_write_cstring(data_phys, 64, "user task exit=42\n".c_str())
    vmm_unmap_page_root(vmm_state, user_cr3, pmm_state, user_task_code_virt(task_id))
    vmm_unmap_page_root(vmm_state, user_cr3, pmm_state, user_task_stack_virt(task_id))
    vmm_unmap_page_root(vmm_state, user_cr3, pmm_state, user_task_data_virt(task_id))
    vmm_map_page_root(vmm_state, user_cr3, pmm_state, user_task_code_virt(task_id), code_phys, 0x005)
    vmm_map_page_root(vmm_state, user_cr3, pmm_state, user_task_stack_virt(task_id), stack_phys, 0x007)
    vmm_map_page_root(vmm_state, user_cr3, pmm_state, user_task_data_virt(task_id), data_phys, 0x005)

    ctx_ptr, stack_base = scheduler_prepare_user_task_context(task_id, user_task_code_virt(task_id), user_task_stack_top(task_id))
    scheduler_set_task(task_table_ptr, task_id, task_state_runnable(), name_tag, ctx_ptr, stack_base, task_mode_user(), user_cr3, user_base, user_limit)
    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), task_id + 1)
    scheduler_enqueue_task(state_ptr, task_id)
    return task_id


def scheduler_init_bootstrap_tasks(state_ptr: int, pmm_state: int, vmm_state: int):
    task_table_ptr = scheduler_task_table_ptr(state_ptr)
    kernel_cr3 = vmm_state_qword(vmm_state, 1)

    idle_ctx_ptr, idle_stack_base = scheduler_prepare_kernel_task_context(0)
    task1_ctx_ptr, task1_stack_base = scheduler_prepare_kernel_task_context(1)

    scheduler_set_task(task_table_ptr, 0, task_state_runnable(), 0, idle_ctx_ptr, idle_stack_base, task_mode_kernel(), kernel_cr3, 0, 0)
    scheduler_set_task(task_table_ptr, 1, task_state_runnable(), 1, task1_ctx_ptr, task1_stack_base, task_mode_kernel(), kernel_cr3, 0, 0)

    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), 2)
    set_scheduler_state_qword(state_ptr, sched_slot_current_task(), 1)
    set_scheduler_state_qword(state_ptr, sched_slot_idle_task(), 0)

    scheduler_enqueue_task(state_ptr, 0)
    scheduler_record_switch(state_ptr, 1)


def init_scheduler(pmm_state: int, vmm_state: int):
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
    set_scheduler_state_qword(state_ptr, sched_slot_pmm_state(), pmm_state)
    set_scheduler_state_qword(state_ptr, sched_slot_vmm_state(), vmm_state)

    scheduler_init_bootstrap_tasks(state_ptr, pmm_state, vmm_state)
    set_active_scheduler(state_ptr)
    return state_ptr


def scheduler_enter_first_task(state_ptr: int):
    current_task = scheduler_current_task(state_ptr)
    set_tss_rsp0(task_kernel_rsp0_top(scheduler_task_stack_base(state_ptr, current_task)))
    load_cr3(scheduler_task_cr3(state_ptr, current_task))
    restore_task_context(scheduler_task_context_ptr(state_ptr, current_task))
    panic("scheduler failed to enter first task".c_str())


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


def scheduler_switch_to_task(state_ptr: int, old_task: int, next_task: int):
    if next_task == old_task:
        return next_task

    old_ctx_ptr = scheduler_task_context_ptr(state_ptr, old_task)
    new_ctx_ptr = scheduler_task_context_ptr(state_ptr, next_task)
    set_tss_rsp0(task_kernel_rsp0_top(scheduler_task_stack_base(state_ptr, next_task)))
    load_cr3(scheduler_task_cr3(state_ptr, next_task))
    context_switch(old_ctx_ptr, new_ctx_ptr)
    return scheduler_current_task(state_ptr)


def scheduler_yield_current_task(state_ptr: int):
    old_task = scheduler_current_task(state_ptr)
    next_task = scheduler_pick_next_task(state_ptr)
    return scheduler_switch_to_task(state_ptr, old_task, next_task)


def scheduler_exit_current_task(state_ptr: int, exit_code: int):
    current_task = scheduler_current_task(state_ptr)
    if current_task == scheduler_idle_task(state_ptr):
        panic("cannot exit idle task".c_str())

    scheduler_set_task_state(state_ptr, current_task, task_state_exited())
    scheduler_set_task_exit_code(state_ptr, current_task, exit_code)
    next_task = scheduler_pick_next_task(state_ptr)
    scheduler_switch_to_task(state_ptr, current_task, next_task)
    panic("exited task resumed".c_str())


def scheduler_waitpid(state_ptr: int, task_id: int):
    if task_id < 0 or task_id >= scheduler_task_count(state_ptr):
        panic("waitpid task id out of range".c_str())

    while scheduler_task_state(state_ptr, task_id) != task_state_exited():
        scheduler_yield_current_task(state_ptr)

    return scheduler_task_exit_code(state_ptr, task_id)


def scheduler_runnable_count(state_ptr: int):
    task_id = 0
    runnable = 0
    while task_id < scheduler_task_count(state_ptr):
        if scheduler_task_state(state_ptr, task_id) == task_state_runnable():
            runnable += 1
        task_id += 1
    return runnable


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
    console_write(" mode=".c_str())
    console_write_u64(scheduler_task_mode(state_ptr, task_id))
    console_write(" wait=".c_str())
    console_write_u64(scheduler_task_wait_ticks(state_ptr, task_id))
    console_write(" user=[".c_str())
    console_write_u64(scheduler_task_user_base(state_ptr, task_id))
    console_write(",".c_str())
    console_write_u64(scheduler_task_user_limit(state_ptr, task_id))
    console_write(")".c_str())
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

from kconsole import console_write
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from kelf import elf_pf_w
from kelf import elf_user_image_page_count
from kelf import elf_user_load_segment_count
from kelf import elf_user_segment_filesz
from kelf import elf_user_segment_flags
from kelf import elf_user_segment_memsz
from kelf import elf_user_segment_offset
from kelf import elf_user_segment_vaddr
from kelf import elf_user_entry_offset
from kelf import elf_validate_user_image
from khal import context_switch
from khal import load_cr3
from khal import restore_task_context
from khal import set_active_scheduler
from khal import set_tss_rsp0
from khal import task_trampoline_addr
from khal import user_task_trampoline_addr
from kmemory import pmm_alloc_page
from kmemory import pmm_free_page
from kmemory import vmm_clone_kernel_address_space
from kmemory import vmm_free_cloned_address_space
from kmemory import vmm_map_page_root
from kmemory import vmm_state_qword
from kmemory import vmm_translate_root
from kmemory import vmm_unmap_page_root
from kmemory import zero_page
from kvfs import vfs_alloc_console_in_descriptor
from kvfs import vfs_alloc_console_out_descriptor
from kvfs import vfs_close_descriptor
from ksupport import align_down
from ksupport import alloc_bytes
from ksupport import load_byte_region
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_byte_region
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


def task_slot_user_page_array_ptr():
    return 13


def task_slot_user_page_count():
    return 14


def task_slot_user_stack_phys():
    return 15


def task_slot_fd0_kind():
    return 16


def task_slot_fd1_kind():
    return 17


def task_slot_fd2_kind():
    return 18


def task_slot_fd3_kind():
    return 19


def task_slot_parent_pid():
    return 20


def task_slot_limit():
    return 21


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


def task_fd_kind_closed():
    return 0


def task_fd_kind_console_in():
    return 1


def task_fd_kind_console_out():
    return 2


def max_tasks():
    return 8


def ready_queue_capacity():
    return 16


def task_stack_size():
    return 4096


def user_task_region_base(task_id: int):
    return 0x20000000 + task_id * 0x200000


def user_task_region_size():
    return 0x200000


def user_page_size():
    return 4096


def max_user_mapped_pages():
    return 65


def user_task_page_virt(task_id: int, page_index: int):
    return user_task_region_base(task_id) + page_index * user_page_size()


def user_task_stack_base_virt(task_id: int, page_count: int):
    return user_task_page_virt(task_id, page_count - 1)


def user_task_stack_top(task_id: int, page_count: int):
    return user_task_page_virt(task_id, page_count)


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


def sched_slot_vfs_state():
    return 14


def sched_slot_limit():
    return 15


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


def scheduler_task_user_page_array_ptr(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_user_page_array_ptr())


def scheduler_task_user_page_count(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_user_page_count())


def scheduler_task_user_stack_phys(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_user_stack_phys())


def scheduler_task_parent_pid(state_ptr: int, task_id: int):
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_parent_pid())


def scheduler_pmm_state(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_pmm_state())


def scheduler_vmm_state(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_vmm_state())


def scheduler_vfs_state(state_ptr: int):
    return scheduler_state_qword(state_ptr, sched_slot_vfs_state())


def scheduler_set_task_state(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_state(), value)


def scheduler_set_task_wait_ticks(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_wait_ticks(), value)


def scheduler_set_task_exit_code(state_ptr: int, task_id: int, value: int):
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, task_slot_exit_code(), value)


def task_fd_slot(fd: int):
    if fd == 0:
        return task_slot_fd0_kind()
    if fd == 1:
        return task_slot_fd1_kind()
    if fd == 2:
        return task_slot_fd2_kind()
    if fd == 3:
        return task_slot_fd3_kind()
    return -1


def scheduler_task_fd_object(state_ptr: int, task_id: int, fd: int):
    slot = task_fd_slot(fd)
    if slot < 0:
        return 0
    return scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, slot)


def scheduler_set_task_fd_object(state_ptr: int, task_id: int, fd: int, desc_id: int):
    slot = task_fd_slot(fd)
    if slot < 0:
        panic("task fd out of range".c_str())
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), task_id, slot, desc_id)


def scheduler_init_task_fds(state_ptr: int, task_id: int):
    vfs_state = scheduler_vfs_state(state_ptr)
    fd0 = vfs_alloc_console_in_descriptor(vfs_state)
    fd1 = vfs_alloc_console_out_descriptor(vfs_state)
    fd2 = vfs_alloc_console_out_descriptor(vfs_state)

    if fd0 == 0 or fd1 == 0 or fd2 == 0:
        panic("task fd alloc failed".c_str())

    scheduler_set_task_fd_object(state_ptr, task_id, 0, fd0)
    scheduler_set_task_fd_object(state_ptr, task_id, 1, fd1)
    scheduler_set_task_fd_object(state_ptr, task_id, 2, fd2)
    scheduler_set_task_fd_object(state_ptr, task_id, 3, 0)


def scheduler_release_task_fds(state_ptr: int, task_id: int):
    vfs_state = scheduler_vfs_state(state_ptr)
    fd = 0
    while fd < 4:
        desc_id = scheduler_task_fd_object(state_ptr, task_id, fd)
        if desc_id != 0:
            vfs_close_descriptor(vfs_state, desc_id)
            scheduler_set_task_fd_object(state_ptr, task_id, fd, 0)
        fd += 1


def scheduler_clear_task(task_table_ptr: int, task_id: int):
    slot = 0
    while slot < task_slot_limit():
        set_scheduler_task_qword(task_table_ptr, task_id, slot, 0)
        slot += 1


def scheduler_set_task(state_ptr: int, task_id: int, state: int, name_tag: int, ctx_ptr: int, stack_base: int, mode: int, cr3: int, user_base: int, user_limit: int, user_page_array_ptr: int, user_page_count: int, user_stack_phys: int, parent_pid: int):
    task_table_ptr = scheduler_task_table_ptr(state_ptr)
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
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_user_page_array_ptr(), user_page_array_ptr)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_user_page_count(), user_page_count)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_user_stack_phys(), user_stack_phys)
    set_scheduler_task_qword(task_table_ptr, task_id, task_slot_parent_pid(), parent_pid)
    scheduler_init_task_fds(state_ptr, task_id)


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


def scheduler_configure_user_task_context(ctx_ptr: int, stack_base: int, task_id: int, user_rip: int, user_rsp: int, argc: int, argv_ptr: int, envp_ptr: int):
    stack_top = align_down(stack_base + task_stack_size(), 16)
    initial_rsp = stack_top - 8

    store_qword_region(initial_rsp, 1, 0, user_task_trampoline_addr())
    set_task_context_qword(ctx_ptr, context_slot_rsp(), initial_rsp)
    set_task_context_qword(ctx_ptr, context_slot_rbx(), argc)
    set_task_context_qword(ctx_ptr, context_slot_rbp(), argv_ptr)
    set_task_context_qword(ctx_ptr, context_slot_r12(), user_rip)
    set_task_context_qword(ctx_ptr, context_slot_r13(), user_rsp)
    set_task_context_qword(ctx_ptr, context_slot_r14(), envp_ptr)
    set_task_context_qword(ctx_ptr, context_slot_r15(), 0)
    return ctx_ptr, stack_base


def scheduler_prepare_user_task_context(task_id: int, user_rip: int, user_rsp: int, argc: int, argv_ptr: int, envp_ptr: int):
    ctx_ptr = alloc_bytes(context_slot_limit() * 8)
    stack_base = alloc_bytes(task_stack_size())
    return scheduler_configure_user_task_context(ctx_ptr, stack_base, task_id, user_rip, user_rsp, argc, argv_ptr, envp_ptr)


def exec_vec_entry_ptr(vec_ptr: int, index: int):
    return vec_ptr + index * 16


def exec_vec_arg_ptr(vec_ptr: int, index: int):
    return load_qword_region(exec_vec_entry_ptr(vec_ptr, index), 2, 0)


def exec_vec_arg_len(vec_ptr: int, index: int):
    return load_qword_region(exec_vec_entry_ptr(vec_ptr, index), 2, 1)


def scheduler_copy_stack_string(stack_phys: int, stack_top_off: int, src_ptr: int, src_len: int):
    copied = 0
    stack_top_off -= src_len + 1
    while copied < src_len:
        store_byte_region(stack_phys, user_page_size(), stack_top_off + copied, load_byte_region(src_ptr, src_len, copied))
        copied += 1
    store_byte_region(stack_phys, user_page_size(), stack_top_off + src_len, 0)
    return stack_top_off


def scheduler_build_user_initial_stack(task_id: int, page_count: int, page_array_ptr: int, argvec_ptr: int, arg_count: int, envvec_ptr: int, env_count: int):
    stack_phys = user_page_array_qword(page_array_ptr, page_count, page_count - 1)
    stack_base = user_task_stack_base_virt(task_id, page_count)
    arg_user_ptrs = 0
    env_user_ptrs = 0
    stack_top_off = user_page_size()
    argv_ptr = 0
    envp_ptr = 0
    index = 0

    if arg_count > 0:
        arg_user_ptrs = alloc_bytes(arg_count * 8)
    if env_count > 0:
        env_user_ptrs = alloc_bytes(env_count * 8)

    index = env_count - 1
    while index >= 0:
        stack_top_off = scheduler_copy_stack_string(stack_phys, stack_top_off, exec_vec_arg_ptr(envvec_ptr, index), exec_vec_arg_len(envvec_ptr, index))
        store_qword_region(env_user_ptrs, env_count, index, stack_base + stack_top_off)
        index -= 1

    index = arg_count - 1
    while index >= 0:
        stack_top_off = scheduler_copy_stack_string(stack_phys, stack_top_off, exec_vec_arg_ptr(argvec_ptr, index), exec_vec_arg_len(argvec_ptr, index))
        store_qword_region(arg_user_ptrs, arg_count, index, stack_base + stack_top_off)
        index -= 1

    stack_top_off = align_down(stack_top_off, 16)
    stack_top_off -= (env_count + 1) * 8
    envp_ptr = stack_base + stack_top_off
    index = 0
    while index < env_count:
        store_qword_region(stack_phys + stack_top_off, env_count + 1, index, load_qword_region(env_user_ptrs, env_count, index))
        index += 1
    store_qword_region(stack_phys + stack_top_off, env_count + 1, env_count, 0)

    stack_top_off -= (arg_count + 1) * 8
    argv_ptr = stack_base + stack_top_off
    index = 0
    while index < arg_count:
        store_qword_region(stack_phys + stack_top_off, arg_count + 1, index, load_qword_region(arg_user_ptrs, arg_count, index))
        index += 1
    store_qword_region(stack_phys + stack_top_off, arg_count + 1, arg_count, 0)

    stack_top_off -= 8
    store_qword_region(stack_phys + stack_top_off, 1, 0, arg_count)
    return stack_base + stack_top_off, arg_count, argv_ptr, envp_ptr


def user_page_array_qword(page_array_ptr: int, page_count: int, slot: int):
    return load_qword_region(page_array_ptr, page_count, slot)


def set_user_page_array_qword(page_array_ptr: int, page_count: int, slot: int, value: int):
    store_qword_region(page_array_ptr, page_count, slot, value)


def scheduler_user_page_flags_default():
    return 0x005


def scheduler_user_page_flags_writable():
    return 0x007


def scheduler_user_image_total_pages(image_ptr: int, image_len: int):
    return elf_user_image_page_count(image_ptr, image_len) + 1


def scheduler_set_page_flags(page_flags_ptr: int, image_page_count: int, page_index: int, value: int):
    store_qword_region(page_flags_ptr, image_page_count, page_index, value)


def scheduler_page_flags(page_flags_ptr: int, image_page_count: int, page_index: int):
    return load_qword_region(page_flags_ptr, image_page_count, page_index)


def scheduler_prepare_user_image_pages(state_ptr: int, task_id: int, pmm_state: int, image_ptr: int, image_len: int):
    image_page_count = elf_user_image_page_count(image_ptr, image_len)
    page_count = image_page_count + 1
    page_array_ptr = alloc_bytes(page_count * 8)
    page_flags_ptr = alloc_bytes(image_page_count * 8)
    load_index = 0
    page_index = 0

    if page_count <= 1 or page_count > max_user_mapped_pages():
        panic("user image page count invalid".c_str())

    while page_index < image_page_count:
        scheduler_set_page_flags(page_flags_ptr, image_page_count, page_index, scheduler_user_page_flags_default())
        page_index += 1

    page_index = 0
    while page_index < page_count:
        phys = pmm_alloc_page(pmm_state)
        if phys == 0:
            panic("scheduler user image alloc failed".c_str())
        zero_page(phys)
        set_user_page_array_qword(page_array_ptr, page_count, page_index, phys)
        page_index += 1

    while load_index < elf_user_load_segment_count(image_ptr, image_len):
        seg_offset = elf_user_segment_offset(image_ptr, image_len, load_index)
        seg_vaddr = elf_user_segment_vaddr(image_ptr, image_len, load_index)
        seg_filesz = elf_user_segment_filesz(image_ptr, image_len, load_index)
        seg_memsz = elf_user_segment_memsz(image_ptr, image_len, load_index)
        seg_flags = elf_user_segment_flags(image_ptr, image_len, load_index)
        seg_page = seg_vaddr >> 12
        seg_page_end = align_down(seg_vaddr + seg_memsz + user_page_size() - 1, user_page_size()) >> 12
        copied = 0

        if (seg_flags & elf_pf_w()) != 0:
            page_index = seg_page
            while page_index < seg_page_end:
                scheduler_set_page_flags(page_flags_ptr, image_page_count, page_index, scheduler_user_page_flags_writable())
                page_index += 1

        while copied < seg_filesz:
            page_index = (seg_vaddr + copied) >> 12
            page_off = (seg_vaddr + copied) & (user_page_size() - 1)
            phys = user_page_array_qword(page_array_ptr, page_count, page_index)
            store_byte_region(phys, user_page_size(), page_off, load_byte_region(image_ptr, image_len, seg_offset + copied))
            copied += 1
        load_index += 1

    return page_array_ptr, page_count, page_flags_ptr


def scheduler_map_user_image_pages(state_ptr: int, task_id: int, root_p4: int, pmm_state: int, page_array_ptr: int, page_count: int, page_flags_ptr: int):
    page_index = 0
    image_page_count = page_count - 1
    vmm_state = scheduler_vmm_state(state_ptr)
    virt = 0

    while page_index < image_page_count:
        virt = user_task_page_virt(task_id, page_index)
        if vmm_translate_root(vmm_state, root_p4, virt) != 0:
            vmm_unmap_page_root(vmm_state, root_p4, pmm_state, virt)
        vmm_map_page_root(vmm_state, root_p4, pmm_state, virt, user_page_array_qword(page_array_ptr, page_count, page_index), scheduler_page_flags(page_flags_ptr, image_page_count, page_index))
        page_index += 1

    virt = user_task_stack_base_virt(task_id, page_count)
    if vmm_translate_root(vmm_state, root_p4, virt) != 0:
        vmm_unmap_page_root(vmm_state, root_p4, pmm_state, virt)
    vmm_map_page_root(vmm_state, root_p4, pmm_state, virt, user_page_array_qword(page_array_ptr, page_count, page_count - 1), scheduler_user_page_flags_writable())


def scheduler_unmap_user_image_pages(state_ptr: int, root_p4: int, pmm_state: int, user_base: int, page_count: int):
    page_index = 0
    vmm_state = scheduler_vmm_state(state_ptr)
    while page_index < page_count:
        vmm_unmap_page_root(vmm_state, root_p4, pmm_state, user_base + page_index * user_page_size())
        page_index += 1


def scheduler_release_user_pages(pmm_state: int, page_array_ptr: int, page_count: int):
    page_index = 0
    while page_index < page_count:
        phys = user_page_array_qword(page_array_ptr, page_count, page_index)
        if phys != 0:
            pmm_free_page(pmm_state, phys)
        page_index += 1


def scheduler_install_user_image(state_ptr: int, task_id: int, root_p4: int, pmm_state: int, image_ptr: int, image_len: int, argvec_ptr: int, arg_count: int, envvec_ptr: int, env_count: int):
    page_array_ptr, page_count, page_flags_ptr = scheduler_prepare_user_image_pages(state_ptr, task_id, pmm_state, image_ptr, image_len)
    user_rsp, user_argc, user_argv_ptr, user_envp_ptr = scheduler_build_user_initial_stack(task_id, page_count, page_array_ptr, argvec_ptr, arg_count, envvec_ptr, env_count)
    scheduler_map_user_image_pages(state_ptr, task_id, root_p4, pmm_state, page_array_ptr, page_count, page_flags_ptr)
    return page_array_ptr, page_count, user_task_region_base(task_id) + elf_user_entry_offset(image_ptr, image_len), user_task_region_base(task_id) + page_count * user_page_size(), user_page_array_qword(page_array_ptr, page_count, page_count - 1), user_rsp, user_argc, user_argv_ptr, user_envp_ptr


def scheduler_replace_current_user_context(state_ptr: int, task_id: int, user_rip: int, user_rsp: int, argc: int, argv_ptr: int, envp_ptr: int):
    ctx_ptr = scheduler_task_context_ptr(state_ptr, task_id)
    stack_base = scheduler_task_stack_base(state_ptr, task_id)
    scheduler_configure_user_task_context(ctx_ptr, stack_base, task_id, user_rip, user_rsp, argc, argv_ptr, envp_ptr)
    set_tss_rsp0(task_kernel_rsp0_top(stack_base))
    load_cr3(scheduler_task_cr3(state_ptr, task_id))
    restore_task_context(ctx_ptr)
    panic("scheduler exec returned".c_str())


def scheduler_user_code_flags(image_ptr: int, image_len: int):
    if (elf_user_segment_flags(image_ptr, image_len, 0) & elf_pf_w()) != 0:
        return 0x007
    return 0x005


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
    task_id = 0
    limit = scheduler_task_count(state_ptr)
    while task_id < limit:
        if scheduler_task_state(state_ptr, task_id) == task_state_empty():
            return task_id
        task_id += 1

    if limit >= max_tasks():
        panic("scheduler task table full".c_str())
    return limit


def scheduler_destroy_user_task(state_ptr: int, task_id: int):
    if scheduler_task_mode(state_ptr, task_id) != task_mode_user():
        return

    pmm_state = scheduler_pmm_state(state_ptr)
    vmm_state = scheduler_vmm_state(state_ptr)
    root_p4 = scheduler_task_cr3(state_ptr, task_id)
    page_array_ptr = scheduler_task_user_page_array_ptr(state_ptr, task_id)
    page_count = scheduler_task_user_page_count(state_ptr, task_id)

    if page_array_ptr != 0 and page_count > 0:
        scheduler_release_user_pages(pmm_state, page_array_ptr, page_count)
    if root_p4 != 0:
        vmm_free_cloned_address_space(vmm_state, pmm_state, root_p4)


def scheduler_release_task_slot(state_ptr: int, task_id: int):
    task_table_ptr = scheduler_task_table_ptr(state_ptr)
    scheduler_release_task_fds(state_ptr, task_id)
    scheduler_clear_task(task_table_ptr, task_id)

    task_count = scheduler_task_count(state_ptr)
    while task_count > 0:
        if scheduler_task_state(state_ptr, task_count - 1) != task_state_empty():
            break
        task_count -= 1
    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), task_count)


def scheduler_create_user_task(state_ptr: int, name_tag: int):
    panic("scheduler_create_user_task is obsolete; use ELF exec path".c_str())


def scheduler_create_user_elf_task(state_ptr: int, name_tag: int, image_ptr: int, image_len: int, argvec_ptr: int, arg_count: int, envvec_ptr: int, env_count: int):
    task_id = scheduler_find_free_task_id(state_ptr)
    pmm_state = scheduler_pmm_state(state_ptr)
    vmm_state = scheduler_vmm_state(state_ptr)
    user_cr3 = vmm_clone_kernel_address_space(vmm_state, pmm_state)
    user_base = user_task_region_base(task_id)
    user_limit = 0
    user_rip = 0
    page_array_ptr = 0
    page_count = 0
    stack_phys = 0
    user_rsp = 0
    user_argc = 0
    user_argv_ptr = 0
    user_envp_ptr = 0

    if not elf_validate_user_image(image_ptr, image_len):
        panic("scheduler invalid user elf".c_str())

    page_array_ptr, page_count, user_rip, user_limit, stack_phys, user_rsp, user_argc, user_argv_ptr, user_envp_ptr = scheduler_install_user_image(state_ptr, task_id, user_cr3, pmm_state, image_ptr, image_len, argvec_ptr, arg_count, envvec_ptr, env_count)
    ctx_ptr, stack_base = scheduler_prepare_user_task_context(task_id, user_rip, user_rsp, user_argc, user_argv_ptr, user_envp_ptr)
    scheduler_set_task(state_ptr, task_id, task_state_runnable(), name_tag, ctx_ptr, stack_base, task_mode_user(), user_cr3, user_base, user_limit, page_array_ptr, page_count, stack_phys, scheduler_current_task(state_ptr))
    if task_id >= scheduler_task_count(state_ptr):
        set_scheduler_state_qword(state_ptr, sched_slot_task_count(), task_id + 1)
    scheduler_enqueue_task(state_ptr, task_id)
    return task_id


def scheduler_exec_current_task(state_ptr: int, image_ptr: int, image_len: int, argvec_ptr: int, arg_count: int, envvec_ptr: int, env_count: int):
    current_task = scheduler_current_task(state_ptr)
    pmm_state = scheduler_pmm_state(state_ptr)
    root_p4 = scheduler_task_cr3(state_ptr, current_task)
    old_page_array_ptr = scheduler_task_user_page_array_ptr(state_ptr, current_task)
    old_page_count = scheduler_task_user_page_count(state_ptr, current_task)
    user_base = scheduler_task_user_base(state_ptr, current_task)
    page_array_ptr = 0
    page_count = 0
    user_rip = 0
    user_limit = 0
    stack_phys = 0
    page_flags_ptr = 0
    user_rsp = 0
    user_argc = 0
    user_argv_ptr = 0
    user_envp_ptr = 0

    if scheduler_task_mode(state_ptr, current_task) != task_mode_user():
        return -1
    if not elf_validate_user_image(image_ptr, image_len):
        return -1

    page_array_ptr, page_count, page_flags_ptr = scheduler_prepare_user_image_pages(state_ptr, current_task, pmm_state, image_ptr, image_len)
    user_rsp, user_argc, user_argv_ptr, user_envp_ptr = scheduler_build_user_initial_stack(current_task, page_count, page_array_ptr, argvec_ptr, arg_count, envvec_ptr, env_count)
    if old_page_array_ptr != 0 and old_page_count > 0:
        scheduler_unmap_user_image_pages(state_ptr, root_p4, pmm_state, user_base, old_page_count)
        scheduler_release_user_pages(pmm_state, old_page_array_ptr, old_page_count)
    scheduler_map_user_image_pages(state_ptr, current_task, root_p4, pmm_state, page_array_ptr, page_count, page_flags_ptr)
    user_rip = user_task_region_base(current_task) + elf_user_entry_offset(image_ptr, image_len)
    user_limit = user_task_region_base(current_task) + page_count * user_page_size()
    stack_phys = user_page_array_qword(page_array_ptr, page_count, page_count - 1)

    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), current_task, task_slot_user_page_array_ptr(), page_array_ptr)
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), current_task, task_slot_user_page_count(), page_count)
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), current_task, task_slot_user_limit(), user_limit)
    set_scheduler_task_qword(scheduler_task_table_ptr(state_ptr), current_task, task_slot_user_stack_phys(), stack_phys)
    scheduler_replace_current_user_context(state_ptr, current_task, user_rip, user_rsp, user_argc, user_argv_ptr, user_envp_ptr)
    return 0


def scheduler_init_bootstrap_tasks(state_ptr: int, pmm_state: int, vmm_state: int):
    kernel_cr3 = vmm_state_qword(vmm_state, 1)

    idle_ctx_ptr, idle_stack_base = scheduler_prepare_kernel_task_context(0)
    task1_ctx_ptr, task1_stack_base = scheduler_prepare_kernel_task_context(1)

    scheduler_set_task(state_ptr, 0, task_state_runnable(), 0, idle_ctx_ptr, idle_stack_base, task_mode_kernel(), kernel_cr3, 0, 0, 0, 0, 0, 0)
    scheduler_set_task(state_ptr, 1, task_state_runnable(), 1, task1_ctx_ptr, task1_stack_base, task_mode_kernel(), kernel_cr3, 0, 0, 0, 0, 0, 0)

    set_scheduler_state_qword(state_ptr, sched_slot_task_count(), 2)
    set_scheduler_state_qword(state_ptr, sched_slot_current_task(), 1)
    set_scheduler_state_qword(state_ptr, sched_slot_idle_task(), 0)

    scheduler_enqueue_task(state_ptr, 0)
    scheduler_record_switch(state_ptr, 1)


def init_scheduler(pmm_state: int, vmm_state: int, vfs_state: int):
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
    set_scheduler_state_qword(state_ptr, sched_slot_vfs_state(), vfs_state)

    task_id = 0
    while task_id < max_tasks():
        scheduler_clear_task(task_table_ptr, task_id)
        task_id += 1

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


def scheduler_timer_interrupt(state_ptr: int, allow_preempt: int):
    now = current_kernel_ticks()
    delta = scheduler_account_tick(state_ptr, now)
    if delta == 0:
        return scheduler_current_task(state_ptr)
    if allow_preempt == 0:
        return scheduler_current_task(state_ptr)
    if scheduler_runnable_count(state_ptr) <= 1:
        return scheduler_current_task(state_ptr)
    return scheduler_yield_current_task(state_ptr)


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
    current_task = scheduler_current_task(state_ptr)
    if task_id < 0 or task_id >= scheduler_task_count(state_ptr):
        return -1
    if task_id == current_task:
        return -1
    if scheduler_task_state(state_ptr, task_id) == task_state_empty():
        return -1
    if scheduler_task_parent_pid(state_ptr, task_id) != current_task:
        return -1

    while scheduler_task_state(state_ptr, task_id) != task_state_exited():
        scheduler_yield_current_task(state_ptr)

    status = scheduler_task_exit_code(state_ptr, task_id)
    scheduler_destroy_user_task(state_ptr, task_id)
    scheduler_release_task_slot(state_ptr, task_id)
    return status


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

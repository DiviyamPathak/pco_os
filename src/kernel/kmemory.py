from khal import load_cr3
from khal import read_cr3
from kboot import boot_info_qword
from kconsole import console_write
from kconsole import console_write_label_hex
from kconsole import console_write_label_u64
from kconsole import console_write_line
from kconsole import console_write_u64
from kconsole import console_write_hex
from ksupport import align_down
from ksupport import align_up
from ksupport import alloc_bytes
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_qword_region


def pmm_state_qword(state_ptr: int, slot: int):
    return load_qword_region(state_ptr, 7, slot)


def set_pmm_state_qword(state_ptr: int, slot: int, value: int):
    store_qword_region(state_ptr, 7, slot, value)


def pmm_region_entry_ptr(region_table_ptr: int, index: int):
    if index < 0 or index >= 64:
        panic("pmm region index out of range".c_str())
    return region_table_ptr + index * 16


def pmm_region_start(region_table_ptr: int, index: int):
    return load_qword_region(pmm_region_entry_ptr(region_table_ptr, index), 2, 0)


def pmm_region_end(region_table_ptr: int, index: int):
    return load_qword_region(pmm_region_entry_ptr(region_table_ptr, index), 2, 1)


def set_pmm_region(region_table_ptr: int, index: int, start: int, end: int):
    entry_ptr = pmm_region_entry_ptr(region_table_ptr, index)
    store_qword_region(entry_ptr, 2, 0, start)
    store_qword_region(entry_ptr, 2, 1, end)


def pmm_stack_push(stack_ptr: int, index: int, value: int):
    store_qword_region(stack_ptr, 2048, index, value)


def pmm_stack_pop(stack_ptr: int, index: int):
    return load_qword_region(stack_ptr, 2048, index)


def pmm_add_region(state_ptr: int, start: int, end: int):
    if start >= end:
        return

    pages = (end - start) >> 12
    if pages == 0:
        return

    region_count = pmm_state_qword(state_ptr, 1)
    if region_count >= 64:
        panic("pmm region table full".c_str())

    region_table_ptr = pmm_state_qword(state_ptr, 0)
    set_pmm_region(region_table_ptr, region_count, start, end)
    set_pmm_state_qword(state_ptr, 1, region_count + 1)
    set_pmm_state_qword(state_ptr, 5, pmm_state_qword(state_ptr, 5) + pages)
    set_pmm_state_qword(state_ptr, 6, pmm_state_qword(state_ptr, 6) + pages)


def init_pmm(boot_info_ptr: int):
    mmap_ptr = boot_info_qword(boot_info_ptr, 3)
    mmap_count = boot_info_qword(boot_info_ptr, 4)
    kernel_start = align_down(boot_info_qword(boot_info_ptr, 13), 4096)
    kernel_end = align_up(boot_info_qword(boot_info_ptr, 14), 4096)
    state_ptr = alloc_bytes(7 * 8)
    region_table_ptr = alloc_bytes(64 * 16)
    recycle_stack_ptr = alloc_bytes(2048 * 8)

    if mmap_ptr == 0 or mmap_count == 0:
        panic("pmm requires a boot memory map".c_str())

    set_pmm_state_qword(state_ptr, 0, region_table_ptr)
    set_pmm_state_qword(state_ptr, 1, 0)
    set_pmm_state_qword(state_ptr, 2, 0)
    set_pmm_state_qword(state_ptr, 3, recycle_stack_ptr)
    set_pmm_state_qword(state_ptr, 4, 0)
    set_pmm_state_qword(state_ptr, 5, 0)
    set_pmm_state_qword(state_ptr, 6, 0)

    entry_index = 0
    while entry_index < mmap_count:
        entry = mmap_ptr + entry_index * 32
        base = load_qword_region(entry, 4, 0)
        length = load_qword_region(entry, 4, 1)
        entry_type = load_qword_region(entry, 4, 2)

        if entry_type == 7 and length != 0:
            start = align_up(base, 4096)
            end = align_down(base + length, 4096)

            if end > 0x100000:
                if start < 0x100000:
                    start = 0x100000

                if start < kernel_start and end > kernel_start:
                    pmm_add_region(state_ptr, start, kernel_start)
                    start = kernel_end
                elif start >= kernel_start and start < kernel_end:
                    start = kernel_end

                if start < end:
                    pmm_add_region(state_ptr, start, end)

        entry_index += 1

    if pmm_state_qword(state_ptr, 1) == 0:
        panic("pmm found no usable regions".c_str())

    return state_ptr


def pmm_alloc_page(state_ptr: int):
    free_pages = pmm_state_qword(state_ptr, 6)
    if free_pages == 0:
        return 0

    recycle_count = pmm_state_qword(state_ptr, 4)
    if recycle_count != 0:
        recycle_count -= 1
        stack_ptr = pmm_state_qword(state_ptr, 3)
        page = pmm_stack_pop(stack_ptr, recycle_count)
        set_pmm_state_qword(state_ptr, 4, recycle_count)
        set_pmm_state_qword(state_ptr, 6, free_pages - 1)
        return page

    region_index = pmm_state_qword(state_ptr, 2)
    region_count = pmm_state_qword(state_ptr, 1)
    region_table_ptr = pmm_state_qword(state_ptr, 0)

    while region_index < region_count:
        start = pmm_region_start(region_table_ptr, region_index)
        end = pmm_region_end(region_table_ptr, region_index)

        if start + 4096 <= end:
            next_page = start + 4096
            set_pmm_region(region_table_ptr, region_index, next_page, end)
            if next_page >= end:
                set_pmm_state_qword(state_ptr, 2, region_index + 1)
            set_pmm_state_qword(state_ptr, 6, free_pages - 1)
            return start

        region_index += 1
        set_pmm_state_qword(state_ptr, 2, region_index)

    return 0


def pmm_free_page(state_ptr: int, page: int):
    if page == 0:
        panic("cannot free null page".c_str())

    if (page & 0xFFF) != 0:
        panic("cannot free unaligned page".c_str())

    recycle_count = pmm_state_qword(state_ptr, 4)
    if recycle_count >= 2048:
        panic("pmm recycle stack full".c_str())

    stack_ptr = pmm_state_qword(state_ptr, 3)
    pmm_stack_push(stack_ptr, recycle_count, page)
    set_pmm_state_qword(state_ptr, 4, recycle_count + 1)
    set_pmm_state_qword(state_ptr, 6, pmm_state_qword(state_ptr, 6) + 1)


def dump_pmm_summary(state_ptr: int):
    console_write_label_u64("pmm.regions=".c_str(), pmm_state_qword(state_ptr, 1))
    console_write_label_u64("pmm.total_pages=".c_str(), pmm_state_qword(state_ptr, 5))
    console_write_label_u64("pmm.free_pages=".c_str(), pmm_state_qword(state_ptr, 6))

    region_table_ptr = pmm_state_qword(state_ptr, 0)
    region_count = pmm_state_qword(state_ptr, 1)
    region_index = 0
    while region_index < region_count and region_index < 8:
        console_write("pmm.region[".c_str())
        console_write_u64(region_index)
        console_write("] start=".c_str())
        console_write_hex(pmm_region_start(region_table_ptr, region_index))
        console_write(" end=".c_str())
        console_write_hex(pmm_region_end(region_table_ptr, region_index))
        console_write("\n".c_str())
        region_index += 1


def pmm_self_test(state_ptr: int):
    free_before = pmm_state_qword(state_ptr, 6)
    page0 = pmm_alloc_page(state_ptr)
    page1 = pmm_alloc_page(state_ptr)
    page2 = pmm_alloc_page(state_ptr)

    if page0 == 0 or page1 == 0 or page2 == 0:
        panic("pmm alloc failed".c_str())

    if page0 == page1 or page0 == page2 or page1 == page2:
        panic("pmm returned duplicate pages".c_str())

    if (page0 & 0xFFF) != 0 or (page1 & 0xFFF) != 0 or (page2 & 0xFFF) != 0:
        panic("pmm returned unaligned page".c_str())

    console_write_label_hex("pmm.test.page0=".c_str(), page0)
    console_write_label_hex("pmm.test.page1=".c_str(), page1)
    console_write_label_hex("pmm.test.page2=".c_str(), page2)

    pmm_free_page(state_ptr, page2)
    pmm_free_page(state_ptr, page1)
    pmm_free_page(state_ptr, page0)

    if pmm_state_qword(state_ptr, 6) != free_before:
        panic("pmm free count mismatch".c_str())

    console_write_line("pmm self-test ok".c_str())


def zero_page(page_ptr: int):
    slot = 0
    while slot < 512:
        store_qword_region(page_ptr, 512, slot, 0)
        slot += 1


def copy_page(src_ptr: int, dst_ptr: int):
    slot = 0
    while slot < 512:
        store_qword_region(dst_ptr, 512, slot, load_qword_region(src_ptr, 512, slot))
        slot += 1


def vmm_state_qword(state_ptr: int, slot: int):
    return load_qword_region(state_ptr, 8, slot)


def set_vmm_state_qword(state_ptr: int, slot: int, value: int):
    store_qword_region(state_ptr, 8, slot, value)


def page_table_qword(table_ptr: int, slot: int):
    return load_qword_region(table_ptr, 512, slot)


def set_page_table_qword(table_ptr: int, slot: int, value: int):
    store_qword_region(table_ptr, 512, slot, value)


def vmm_reload_current_cr3():
    load_cr3(read_cr3())


def pml4_index(addr: int):
    return (addr >> 39) & 0x1FF


def pdpt_index(addr: int):
    return (addr >> 30) & 0x1FF


def pd_index(addr: int):
    return (addr >> 21) & 0x1FF


def pt_index(addr: int):
    return (addr >> 12) & 0x1FF


def vmm_p3_ptr(state_ptr: int):
    return vmm_state_qword(state_ptr, 2)


def vmm_root_p3_ptr(root_p4: int):
    p4_entry = page_table_qword(root_p4, 0)
    if (p4_entry & 1) == 0:
        panic("vmm root missing p3".c_str())
    return align_down(p4_entry, 4096)


def copy_page_table(src_ptr: int, dst_ptr: int):
    slot = 0
    while slot < 512:
        set_page_table_qword(dst_ptr, slot, page_table_qword(src_ptr, slot))
        slot += 1


def vmm_clone_kernel_address_space(state_ptr: int, pmm_state: int):
    src_p4 = vmm_state_qword(state_ptr, 1)
    src_p3 = vmm_state_qword(state_ptr, 2)
    p2_count = vmm_state_qword(state_ptr, 3)
    dst_p4 = pmm_alloc_page(pmm_state)
    dst_p3 = pmm_alloc_page(pmm_state)

    if dst_p4 == 0 or dst_p3 == 0:
        panic("vmm clone alloc failed".c_str())

    zero_page(dst_p4)
    zero_page(dst_p3)
    set_page_table_qword(dst_p4, 0, dst_p3 | 0x003)

    table_index = 0
    while table_index < p2_count:
        src_p2 = align_down(page_table_qword(src_p3, table_index), 4096)
        dst_p2 = pmm_alloc_page(pmm_state)
        entry_index = 0
        if dst_p2 == 0:
            panic("vmm clone p2 alloc failed".c_str())

        zero_page(dst_p2)
        while entry_index < 512:
            src_entry = page_table_qword(src_p2, entry_index)
            if (src_entry & 1) == 0 or (src_entry & 0x80) != 0:
                set_page_table_qword(dst_p2, entry_index, src_entry)
            else:
                src_pt = align_down(src_entry, 4096)
                dst_pt = pmm_alloc_page(pmm_state)
                if dst_pt == 0:
                    panic("vmm clone pt alloc failed".c_str())
                copy_page(src_pt, dst_pt)
                set_page_table_qword(dst_p2, entry_index, dst_pt | (src_entry & 0xFFF))
            entry_index += 1

        set_page_table_qword(dst_p3, table_index, dst_p2 | 0x003)
        table_index += 1

    if read_cr3() == src_p4:
        load_cr3(src_p4)
    return dst_p4


def vmm_free_cloned_address_space(state_ptr: int, pmm_state: int, root_p4: int):
    p3_ptr = vmm_root_p3_ptr(root_p4)
    table_index = 0
    while table_index < vmm_state_qword(state_ptr, 3):
        p2_entry = page_table_qword(p3_ptr, table_index)
        if (p2_entry & 1) != 0:
            p2_ptr = align_down(p2_entry, 4096)
            entry_index = 0
            while entry_index < 512:
                p2_leaf = page_table_qword(p2_ptr, entry_index)
                if (p2_leaf & 1) != 0 and (p2_leaf & 0x80) == 0:
                    pmm_free_page(pmm_state, align_down(p2_leaf, 4096))
                entry_index += 1
            pmm_free_page(pmm_state, p2_ptr)
        table_index += 1

    pmm_free_page(pmm_state, p3_ptr)
    pmm_free_page(pmm_state, root_p4)


def vmm_supports_addr(state_ptr: int, virt: int):
    if pml4_index(virt) != 0:
        return False
    return virt < vmm_state_qword(state_ptr, 4)


def vmm_root_supports_addr(limit: int, virt: int):
    if pml4_index(virt) != 0:
        return False
    return virt < limit


def vmm_p2_ptr(state_ptr: int, virt: int):
    p3_ptr = vmm_p3_ptr(state_ptr)
    p3_entry = page_table_qword(p3_ptr, pdpt_index(virt))
    if (p3_entry & 1) == 0:
        return 0
    return align_down(p3_entry, 4096)


def vmm_root_p2_ptr(root_p4: int, virt: int):
    p3_ptr = vmm_root_p3_ptr(root_p4)
    p3_entry = page_table_qword(p3_ptr, pdpt_index(virt))
    if (p3_entry & 1) == 0:
        return 0
    return align_down(p3_entry, 4096)


def vmm_split_large_page(state_ptr: int, pmm_state: int, virt: int):
    if not vmm_supports_addr(state_ptr, virt):
        panic("vmm address outside bootstrap range".c_str())

    p2_ptr = vmm_p2_ptr(state_ptr, virt)
    p2_slot = pd_index(virt)
    p2_entry = page_table_qword(p2_ptr, p2_slot)

    if (p2_entry & 1) == 0:
        panic("vmm missing p2 entry".c_str())

    if (p2_entry & 0x80) == 0:
        return align_down(p2_entry, 4096)

    pt_ptr = pmm_alloc_page(pmm_state)
    if pt_ptr == 0:
        panic("vmm split alloc failed".c_str())

    zero_page(pt_ptr)
    phys_base = align_down(p2_entry, 0x200000)
    entry_index = 0
    while entry_index < 512:
        set_page_table_qword(pt_ptr, entry_index, phys_base + (entry_index << 12) | 0x003)
        entry_index += 1

    set_page_table_qword(p2_ptr, p2_slot, pt_ptr | 0x003)
    vmm_reload_current_cr3()
    return pt_ptr


def vmm_root_split_large_page(root_p4: int, limit: int, pmm_state: int, virt: int):
    if not vmm_root_supports_addr(limit, virt):
        panic("vmm root address outside bootstrap range".c_str())

    p2_ptr = vmm_root_p2_ptr(root_p4, virt)
    p2_slot = pd_index(virt)
    p2_entry = page_table_qword(p2_ptr, p2_slot)

    if (p2_entry & 1) == 0:
        panic("vmm root missing p2 entry".c_str())

    if (p2_entry & 0x80) == 0:
        return align_down(p2_entry, 4096)

    pt_ptr = pmm_alloc_page(pmm_state)
    if pt_ptr == 0:
        panic("vmm root split alloc failed".c_str())

    zero_page(pt_ptr)
    phys_base = align_down(p2_entry, 0x200000)
    entry_index = 0
    while entry_index < 512:
        set_page_table_qword(pt_ptr, entry_index, phys_base + (entry_index << 12) | 0x003)
        entry_index += 1

    set_page_table_qword(p2_ptr, p2_slot, pt_ptr | 0x003)
    if read_cr3() == root_p4:
        load_cr3(root_p4)
    return pt_ptr


def vmm_page_flags(state_ptr: int, virt: int):
    if not vmm_supports_addr(state_ptr, virt):
        return 0

    p2_ptr = vmm_p2_ptr(state_ptr, virt)
    if p2_ptr == 0:
        return 0

    p2_entry = page_table_qword(p2_ptr, pd_index(virt))
    if (p2_entry & 1) == 0:
        return 0

    if (p2_entry & 0x80) != 0:
        return p2_entry & 0xFFF

    pt_ptr = align_down(p2_entry, 4096)
    pte = page_table_qword(pt_ptr, pt_index(virt))
    if (pte & 1) == 0:
        return 0
    return pte & 0xFFF


def vmm_translate(state_ptr: int, virt: int):
    if not vmm_supports_addr(state_ptr, virt):
        return 0

    p2_ptr = vmm_p2_ptr(state_ptr, virt)
    if p2_ptr == 0:
        return 0

    p2_entry = page_table_qword(p2_ptr, pd_index(virt))
    if (p2_entry & 1) == 0:
        return 0

    if (p2_entry & 0x80) != 0:
        return align_down(p2_entry, 0x200000) + (virt & 0x1FFFFF)

    pt_ptr = align_down(p2_entry, 4096)
    pte = page_table_qword(pt_ptr, pt_index(virt))
    if (pte & 1) == 0:
        return 0

    return align_down(pte, 4096) + (virt & 0xFFF)


def vmm_translate_root(state_ptr: int, root_p4: int, virt: int):
    if not vmm_root_supports_addr(vmm_state_qword(state_ptr, 4), virt):
        return 0

    p2_ptr = vmm_root_p2_ptr(root_p4, virt)
    if p2_ptr == 0:
        return 0

    p2_entry = page_table_qword(p2_ptr, pd_index(virt))
    if (p2_entry & 1) == 0:
        return 0

    if (p2_entry & 0x80) != 0:
        return align_down(p2_entry, 0x200000) + (virt & 0x1FFFFF)

    pt_ptr = align_down(p2_entry, 4096)
    pte = page_table_qword(pt_ptr, pt_index(virt))
    if (pte & 1) == 0:
        return 0

    return align_down(pte, 4096) + (virt & 0xFFF)


def vmm_map_page(state_ptr: int, pmm_state: int, virt: int, phys: int, flags: int):
    if (virt & 0xFFF) != 0 or (phys & 0xFFF) != 0:
        panic("vmm map requires 4k alignment".c_str())

    pt_ptr = vmm_split_large_page(state_ptr, pmm_state, virt)
    slot = pt_index(virt)
    if page_table_qword(pt_ptr, slot) != 0:
        panic("vmm map over present entry".c_str())

    set_page_table_qword(pt_ptr, slot, phys | (flags & 0xFFF) | 0x001)
    vmm_reload_current_cr3()


def vmm_map_page_root(state_ptr: int, root_p4: int, pmm_state: int, virt: int, phys: int, flags: int):
    if (virt & 0xFFF) != 0 or (phys & 0xFFF) != 0:
        panic("vmm root map requires 4k alignment".c_str())

    pt_ptr = vmm_root_split_large_page(root_p4, vmm_state_qword(state_ptr, 4), pmm_state, virt)
    if (flags & 0x004) != 0:
        p3_ptr = vmm_root_p3_ptr(root_p4)
        pdpt_slot = pdpt_index(virt)
        p2_ptr = vmm_root_p2_ptr(root_p4, virt)
        p2_slot = pd_index(virt)

        set_page_table_qword(root_p4, 0, page_table_qword(root_p4, 0) | 0x004)
        set_page_table_qword(p3_ptr, pdpt_slot, page_table_qword(p3_ptr, pdpt_slot) | 0x004)
        set_page_table_qword(p2_ptr, p2_slot, page_table_qword(p2_ptr, p2_slot) | 0x004)

    slot = pt_index(virt)
    if page_table_qword(pt_ptr, slot) != 0:
        panic("vmm root map over present entry".c_str())

    set_page_table_qword(pt_ptr, slot, phys | (flags & 0xFFF) | 0x001)
    if read_cr3() == root_p4:
        load_cr3(root_p4)


def vmm_unmap_page_root(state_ptr: int, root_p4: int, pmm_state: int, virt: int):
    if (virt & 0xFFF) != 0:
        panic("vmm root unmap requires 4k alignment".c_str())

    pt_ptr = vmm_root_split_large_page(root_p4, vmm_state_qword(state_ptr, 4), pmm_state, virt)
    slot = pt_index(virt)
    if page_table_qword(pt_ptr, slot) == 0:
        panic("vmm root unmap missing entry".c_str())

    set_page_table_qword(pt_ptr, slot, 0)
    if read_cr3() == root_p4:
        load_cr3(root_p4)


def vmm_unmap_page(state_ptr: int, pmm_state: int, virt: int):
    if (virt & 0xFFF) != 0:
        panic("vmm unmap requires 4k alignment".c_str())

    pt_ptr = vmm_split_large_page(state_ptr, pmm_state, virt)
    slot = pt_index(virt)
    if page_table_qword(pt_ptr, slot) == 0:
        panic("vmm unmap missing entry".c_str())

    set_page_table_qword(pt_ptr, slot, 0)
    vmm_reload_current_cr3()


def vmm_protect_page(state_ptr: int, pmm_state: int, virt: int, flags: int):
    if (virt & 0xFFF) != 0:
        panic("vmm protect requires 4k alignment".c_str())

    pt_ptr = vmm_split_large_page(state_ptr, pmm_state, virt)
    slot = pt_index(virt)
    pte = page_table_qword(pt_ptr, slot)
    if pte == 0:
        panic("vmm protect missing entry".c_str())

    phys = align_down(pte, 4096)
    set_page_table_qword(pt_ptr, slot, phys | (flags & 0xFFF) | 0x001)
    vmm_reload_current_cr3()


def init_vmm(pmm_state: int, boot_info_ptr: int):
    p4 = pmm_alloc_page(pmm_state)
    p3 = pmm_alloc_page(pmm_state)
    state_ptr = alloc_bytes(8 * 8)
    table_index = 0
    old_cr3 = read_cr3()
    p2_count = 4

    if p4 == 0 or p3 == 0:
        panic("vmm bootstrap alloc failed".c_str())

    zero_page(p4)
    zero_page(p3)
    set_page_table_qword(p4, 0, p3 | 0x003)

    while table_index < p2_count:
        p2 = pmm_alloc_page(pmm_state)
        entry_index = 0

        if p2 == 0:
            panic("vmm p2 alloc failed".c_str())

        zero_page(p2)
        set_page_table_qword(p3, table_index, p2 | 0x003)

        while entry_index < 512:
            phys = ((table_index * 512) + entry_index) << 21
            set_page_table_qword(p2, entry_index, phys | 0x083)
            entry_index += 1

        table_index += 1

    set_vmm_state_qword(state_ptr, 0, old_cr3)
    set_vmm_state_qword(state_ptr, 1, p4)
    set_vmm_state_qword(state_ptr, 2, p3)
    set_vmm_state_qword(state_ptr, 3, p2_count)
    set_vmm_state_qword(state_ptr, 4, p2_count * 512 * 0x200000)
    set_vmm_state_qword(state_ptr, 5, boot_info_qword(boot_info_ptr, 13))
    set_vmm_state_qword(state_ptr, 6, boot_info_qword(boot_info_ptr, 14))
    set_vmm_state_qword(state_ptr, 7, 0)

    load_cr3(p4)

    if read_cr3() != p4:
        panic("vmm cr3 switch failed".c_str())

    if boot_info_qword(boot_info_ptr, 0) != 0x50434F424F4F5431:
        panic("vmm lost boot info mapping".c_str())

    set_vmm_state_qword(state_ptr, 7, 1)
    return state_ptr


def dump_vmm_summary(state_ptr: int):
    console_write_label_hex("vmm.old_cr3=".c_str(), vmm_state_qword(state_ptr, 0))
    console_write_label_hex("vmm.new_cr3=".c_str(), vmm_state_qword(state_ptr, 1))
    console_write_label_hex("vmm.p3=".c_str(), vmm_state_qword(state_ptr, 2))
    console_write_label_u64("vmm.p2_tables=".c_str(), vmm_state_qword(state_ptr, 3))
    console_write_label_hex("vmm.identity_limit=".c_str(), vmm_state_qword(state_ptr, 4))
    console_write_label_hex("vmm.kernel.start=".c_str(), vmm_state_qword(state_ptr, 5))
    console_write_label_hex("vmm.kernel.end=".c_str(), vmm_state_qword(state_ptr, 6))


def vmm_self_test(state_ptr: int, pmm_state: int, boot_info_ptr: int):
    test_virt = 0x18000000

    if vmm_state_qword(state_ptr, 7) != 1:
        panic("vmm not marked active".c_str())

    if read_cr3() != vmm_state_qword(state_ptr, 1):
        panic("vmm active cr3 mismatch".c_str())

    if boot_info_qword(boot_info_ptr, 0) != 0x50434F424F4F5431:
        panic("vmm boot info self-test failed".c_str())

    if vmm_translate(state_ptr, test_virt) != test_virt:
        panic("vmm identity translation mismatch".c_str())

    scratch_page = pmm_alloc_page(pmm_state)
    if scratch_page == 0:
        panic("vmm self-test scratch alloc failed".c_str())

    console_write_label_hex("vmm.test.virt=".c_str(), test_virt)
    console_write_label_hex("vmm.test.original=".c_str(), vmm_translate(state_ptr, test_virt))
    console_write_label_hex("vmm.test.scratch=".c_str(), scratch_page)

    vmm_unmap_page(state_ptr, pmm_state, test_virt)
    if vmm_translate(state_ptr, test_virt) != 0:
        panic("vmm unmap failed".c_str())

    vmm_map_page(state_ptr, pmm_state, test_virt, scratch_page, 0x003)
    if vmm_translate(state_ptr, test_virt) != scratch_page:
        panic("vmm remap failed".c_str())

    vmm_protect_page(state_ptr, pmm_state, test_virt, 0x001)
    if (vmm_page_flags(state_ptr, test_virt) & 0x002) != 0:
        panic("vmm protect failed".c_str())

    vmm_protect_page(state_ptr, pmm_state, test_virt, 0x003)
    vmm_unmap_page(state_ptr, pmm_state, test_virt)
    vmm_map_page(state_ptr, pmm_state, test_virt, test_virt, 0x003)

    if vmm_translate(state_ptr, test_virt) != test_virt:
        panic("vmm identity restore failed".c_str())

    pmm_free_page(pmm_state, scratch_page)
    console_write_line("vmm self-test ok".c_str())

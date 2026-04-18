from ksupport import load_byte_region
from ksupport import panic


def elf_magic0():
    return 0x7F


def elf_magic1():
    return 0x45


def elf_magic2():
    return 0x4C


def elf_magic3():
    return 0x46


def elf_class_64():
    return 2


def elf_data_little():
    return 1


def elf_type_exec():
    return 2


def elf_machine_x86_64():
    return 62


def elf_pt_load():
    return 1


def elf_pf_x():
    return 1


def elf_pf_w():
    return 2


def elf_pf_r():
    return 4


def elf_page_size():
    return 4096


def elf_max_user_pages():
    return 64


def elf_align_up(value: int, align: int):
    return (value + align - 1) & ~(align - 1)


def elf_u16(image_ptr: int, image_len: int, offset: int):
    return load_byte_region(image_ptr, image_len, offset) | (load_byte_region(image_ptr, image_len, offset + 1) << 8)


def elf_u32(image_ptr: int, image_len: int, offset: int):
    value = 0
    shift = 0
    i = 0
    while i < 4:
        value |= load_byte_region(image_ptr, image_len, offset + i) << shift
        shift += 8
        i += 1
    return value


def elf_u64(image_ptr: int, image_len: int, offset: int):
    value = 0
    shift = 0
    i = 0
    while i < 8:
        value |= load_byte_region(image_ptr, image_len, offset + i) << shift
        shift += 8
        i += 1
    return value


def elf_validate_header(image_ptr: int, image_len: int):
    if image_len < 64:
        return False
    if load_byte_region(image_ptr, image_len, 0) != elf_magic0():
        return False
    if load_byte_region(image_ptr, image_len, 1) != elf_magic1():
        return False
    if load_byte_region(image_ptr, image_len, 2) != elf_magic2():
        return False
    if load_byte_region(image_ptr, image_len, 3) != elf_magic3():
        return False
    if load_byte_region(image_ptr, image_len, 4) != elf_class_64():
        return False
    if load_byte_region(image_ptr, image_len, 5) != elf_data_little():
        return False
    if elf_u16(image_ptr, image_len, 16) != elf_type_exec():
        return False
    if elf_u16(image_ptr, image_len, 18) != elf_machine_x86_64():
        return False
    return True


def elf_entry_offset(image_ptr: int, image_len: int):
    return elf_u64(image_ptr, image_len, 24)


def elf_phoff(image_ptr: int, image_len: int):
    return elf_u64(image_ptr, image_len, 32)


def elf_phentsize(image_ptr: int, image_len: int):
    return elf_u16(image_ptr, image_len, 54)


def elf_phnum(image_ptr: int, image_len: int):
    return elf_u16(image_ptr, image_len, 56)


def elf_segment_offset(image_ptr: int, image_len: int, ph_index: int):
    return elf_phoff(image_ptr, image_len) + ph_index * elf_phentsize(image_ptr, image_len)


def elf_segment_type(image_ptr: int, image_len: int, ph_index: int):
    return elf_u32(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 0)


def elf_segment_flags(image_ptr: int, image_len: int, ph_index: int):
    return elf_u32(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 4)


def elf_segment_file_offset(image_ptr: int, image_len: int, ph_index: int):
    return elf_u64(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 8)


def elf_segment_vaddr(image_ptr: int, image_len: int, ph_index: int):
    return elf_u64(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 16)


def elf_segment_filesz(image_ptr: int, image_len: int, ph_index: int):
    return elf_u64(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 32)


def elf_segment_memsz(image_ptr: int, image_len: int, ph_index: int):
    return elf_u64(image_ptr, image_len, elf_segment_offset(image_ptr, image_len, ph_index) + 40)


def elf_segment_is_user_load(image_ptr: int, image_len: int, ph_index: int):
    if elf_segment_type(image_ptr, image_len, ph_index) != elf_pt_load():
        return False
    return elf_segment_memsz(image_ptr, image_len, ph_index) > 0


def elf_user_load_segment_count(image_ptr: int, image_len: int):
    ph_index = 0
    load_count = 0
    while ph_index < elf_phnum(image_ptr, image_len):
        if elf_segment_is_user_load(image_ptr, image_len, ph_index):
            load_count += 1
        ph_index += 1
    return load_count


def elf_user_load_segment_ph_index(image_ptr: int, image_len: int, load_index: int):
    ph_index = 0
    current = 0
    while ph_index < elf_phnum(image_ptr, image_len):
        if elf_segment_is_user_load(image_ptr, image_len, ph_index):
            if current == load_index:
                return ph_index
            current += 1
        ph_index += 1
    return -1


def elf_user_segment_vaddr(image_ptr: int, image_len: int, load_index: int):
    ph_index = elf_user_load_segment_ph_index(image_ptr, image_len, load_index)
    if ph_index < 0:
        panic("missing user elf vaddr".c_str())
    return elf_segment_vaddr(image_ptr, image_len, ph_index)


def elf_user_segment_offset(image_ptr: int, image_len: int, load_index: int):
    ph_index = elf_user_load_segment_ph_index(image_ptr, image_len, load_index)
    if ph_index < 0:
        panic("missing user elf segment".c_str())
    return elf_segment_file_offset(image_ptr, image_len, ph_index)


def elf_user_segment_filesz(image_ptr: int, image_len: int, load_index: int):
    ph_index = elf_user_load_segment_ph_index(image_ptr, image_len, load_index)
    if ph_index < 0:
        panic("missing user elf filesz".c_str())
    return elf_segment_filesz(image_ptr, image_len, ph_index)


def elf_user_segment_memsz(image_ptr: int, image_len: int, load_index: int):
    ph_index = elf_user_load_segment_ph_index(image_ptr, image_len, load_index)
    if ph_index < 0:
        panic("missing user elf memsz".c_str())
    return elf_segment_memsz(image_ptr, image_len, ph_index)


def elf_user_segment_flags(image_ptr: int, image_len: int, load_index: int):
    ph_index = elf_user_load_segment_ph_index(image_ptr, image_len, load_index)
    if ph_index < 0:
        panic("missing user elf flags".c_str())
    return elf_segment_flags(image_ptr, image_len, ph_index)


def elf_user_image_top(image_ptr: int, image_len: int):
    load_index = 0
    image_top = 0
    while load_index < elf_user_load_segment_count(image_ptr, image_len):
        seg_top = elf_user_segment_vaddr(image_ptr, image_len, load_index) + elf_user_segment_memsz(image_ptr, image_len, load_index)
        if seg_top > image_top:
            image_top = seg_top
        load_index += 1
    return image_top


def elf_user_image_page_count(image_ptr: int, image_len: int):
    return elf_align_up(elf_user_image_top(image_ptr, image_len), elf_page_size()) >> 12


def elf_entry_in_load_segment(image_ptr: int, image_len: int):
    entry = elf_entry_offset(image_ptr, image_len)
    load_index = 0
    while load_index < elf_user_load_segment_count(image_ptr, image_len):
        seg_start = elf_user_segment_vaddr(image_ptr, image_len, load_index)
        seg_end = seg_start + elf_user_segment_memsz(image_ptr, image_len, load_index)
        if entry >= seg_start and entry < seg_end:
            return True
        load_index += 1
    return False


def elf_validate_user_image(image_ptr: int, image_len: int):
    load_count = 0
    i = 0
    j = 0

    if not elf_validate_header(image_ptr, image_len):
        return False
    if elf_phentsize(image_ptr, image_len) < 56:
        return False

    load_count = elf_user_load_segment_count(image_ptr, image_len)
    if load_count <= 0:
        return False

    i = 0
    while i < load_count:
        seg_offset = elf_user_segment_offset(image_ptr, image_len, i)
        seg_vaddr = elf_user_segment_vaddr(image_ptr, image_len, i)
        seg_filesz = elf_user_segment_filesz(image_ptr, image_len, i)
        seg_memsz = elf_user_segment_memsz(image_ptr, image_len, i)
        seg_page_end = elf_align_up(seg_vaddr + seg_memsz, elf_page_size()) >> 12

        if (seg_vaddr & (elf_page_size() - 1)) != 0:
            return False
        if seg_memsz <= 0 or seg_memsz < seg_filesz:
            return False
        if seg_offset + seg_filesz > image_len:
            return False
        if seg_page_end > elf_max_user_pages():
            return False

        j = i + 1
        while j < load_count:
            other_start = elf_user_segment_vaddr(image_ptr, image_len, j)
            other_end = other_start + elf_user_segment_memsz(image_ptr, image_len, j)
            if seg_vaddr < other_end and other_start < seg_vaddr + seg_memsz:
                return False
            j += 1
        i += 1

    if elf_user_image_page_count(image_ptr, image_len) <= 0:
        return False
    if elf_user_image_page_count(image_ptr, image_len) > elf_max_user_pages():
        return False
    if not elf_entry_in_load_segment(image_ptr, image_len):
        return False
    return True


def elf_user_entry_offset(image_ptr: int, image_len: int):
    if not elf_validate_user_image(image_ptr, image_len):
        panic("invalid user elf".c_str())
    return elf_entry_offset(image_ptr, image_len)

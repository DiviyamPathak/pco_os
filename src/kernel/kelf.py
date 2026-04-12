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


def elf_machine_x86_64():
    return 62


def elf_pt_load():
    return 1


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


def elf_find_first_load_segment(image_ptr: int, image_len: int):
    ph_index = 0
    phnum = elf_phnum(image_ptr, image_len)
    while ph_index < phnum:
        if elf_segment_type(image_ptr, image_len, ph_index) == elf_pt_load():
            return ph_index
        ph_index += 1
    return -1


def elf_validate_user_image(image_ptr: int, image_len: int):
    ph_index = 0
    seg_offset = 0
    seg_vaddr = 0
    seg_filesz = 0
    seg_memsz = 0

    if not elf_validate_header(image_ptr, image_len):
        return False
    if elf_phentsize(image_ptr, image_len) < 56:
        return False

    ph_index = elf_find_first_load_segment(image_ptr, image_len)
    if ph_index < 0:
        return False

    seg_offset = elf_segment_file_offset(image_ptr, image_len, ph_index)
    seg_vaddr = elf_segment_vaddr(image_ptr, image_len, ph_index)
    seg_filesz = elf_segment_filesz(image_ptr, image_len, ph_index)
    seg_memsz = elf_segment_memsz(image_ptr, image_len, ph_index)

    if seg_vaddr != 0:
        return False
    if seg_filesz <= 0 or seg_filesz > 4096:
        return False
    if seg_memsz < seg_filesz or seg_memsz > 4096:
        return False
    if seg_offset + seg_filesz > image_len:
        return False
    if elf_entry_offset(image_ptr, image_len) >= seg_memsz:
        return False
    return True


def elf_user_entry_offset(image_ptr: int, image_len: int):
    if not elf_validate_user_image(image_ptr, image_len):
        panic("invalid user elf".c_str())
    return elf_entry_offset(image_ptr, image_len)


def elf_user_segment_offset(image_ptr: int, image_len: int):
    ph_index = elf_find_first_load_segment(image_ptr, image_len)
    if ph_index < 0:
        panic("missing user elf segment".c_str())
    return elf_segment_file_offset(image_ptr, image_len, ph_index)


def elf_user_segment_filesz(image_ptr: int, image_len: int):
    ph_index = elf_find_first_load_segment(image_ptr, image_len)
    if ph_index < 0:
        panic("missing user elf filesz".c_str())
    return elf_segment_filesz(image_ptr, image_len, ph_index)


def elf_user_segment_memsz(image_ptr: int, image_len: int):
    ph_index = elf_find_first_load_segment(image_ptr, image_len)
    if ph_index < 0:
        panic("missing user elf memsz".c_str())
    return elf_segment_memsz(image_ptr, image_len, ph_index)


def elf_user_segment_flags(image_ptr: int, image_len: int):
    ph_index = elf_find_first_load_segment(image_ptr, image_len)
    if ph_index < 0:
        panic("missing user elf flags".c_str())
    return elf_segment_flags(image_ptr, image_len, ph_index)

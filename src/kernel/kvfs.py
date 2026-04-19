from kboot import boot_info_qword
from kconsole import console_write
from kconsole import console_write_label_hex
from kconsole import console_write_label_u64
from kconsole import console_read_ptr_len
from kconsole import console_write_line
from kconsole import console_write_ptr_len
from ksupport import alloc_bytes
from ksupport import load_byte
from ksupport import load_byte_region
from ksupport import load_qword_region
from ksupport import panic
from ksupport import store_byte
from ksupport import store_qword_region


def initramfs_magic():
    return 0x31534652494F4350


def initramfs_version():
    return 1


def vfs_slot_initramfs_ptr():
    return 0


def vfs_slot_initramfs_size():
    return 1


def vfs_slot_node_table_ptr():
    return 2


def vfs_slot_node_count():
    return 3


def vfs_slot_desc_table_ptr():
    return 4


def vfs_slot_desc_capacity():
    return 5


def vfs_slot_limit():
    return 6


def node_slot_name_ptr():
    return 0


def node_slot_name_len():
    return 1


def node_slot_data_ptr():
    return 2


def node_slot_data_len():
    return 3


def node_slot_kind():
    return 4


def node_slot_flags():
    return 5


def node_slot_data_capacity():
    return 6


def node_slot_limit():
    return 7


def desc_slot_kind():
    return 0


def desc_slot_flags():
    return 1


def desc_slot_node_id():
    return 2


def desc_slot_offset():
    return 3


def desc_slot_path_ptr():
    return 4


def desc_slot_path_len():
    return 5


def desc_slot_limit():
    return 6


def desc_kind_closed():
    return 0


def desc_kind_console_in():
    return 1


def desc_kind_console_out():
    return 2


def desc_kind_initramfs_file():
    return 3


def desc_kind_directory():
    return 4


def vfs_node_kind_file():
    return 1


def vfs_node_kind_directory():
    return 2


def node_flag_writable():
    return 1


def max_vfs_nodes():
    return 32


def max_vfs_descriptors():
    return 32


def vfs_state_qword(state_ptr: int, slot: int):
    return load_qword_region(state_ptr, vfs_slot_limit(), slot)


def set_vfs_state_qword(state_ptr: int, slot: int, value: int):
    store_qword_region(state_ptr, vfs_slot_limit(), slot, value)


def vfs_node_entry_ptr(state_ptr: int, node_id: int):
    if node_id < 0 or node_id >= max_vfs_nodes():
        panic("vfs node id out of range".c_str())
    return vfs_state_qword(state_ptr, vfs_slot_node_table_ptr()) + node_id * node_slot_limit() * 8


def vfs_node_qword(state_ptr: int, node_id: int, slot: int):
    return load_qword_region(vfs_node_entry_ptr(state_ptr, node_id), node_slot_limit(), slot)


def set_vfs_node_qword(state_ptr: int, node_id: int, slot: int, value: int):
    store_qword_region(vfs_node_entry_ptr(state_ptr, node_id), node_slot_limit(), slot, value)


def vfs_desc_entry_ptr(state_ptr: int, desc_id: int):
    capacity = vfs_state_qword(state_ptr, vfs_slot_desc_capacity())
    if desc_id <= 0 or desc_id > capacity:
        panic("vfs desc id out of range".c_str())
    return vfs_state_qword(state_ptr, vfs_slot_desc_table_ptr()) + (desc_id - 1) * desc_slot_limit() * 8


def vfs_desc_qword(state_ptr: int, desc_id: int, slot: int):
    return load_qword_region(vfs_desc_entry_ptr(state_ptr, desc_id), desc_slot_limit(), slot)


def set_vfs_desc_qword(state_ptr: int, desc_id: int, slot: int, value: int):
    store_qword_region(vfs_desc_entry_ptr(state_ptr, desc_id), desc_slot_limit(), slot, value)


def vfs_raw_qword(ptr: int):
    return load_qword_region(ptr, 1, 0)


def vfs_clear_descriptors(state_ptr: int):
    desc_id = 1
    capacity = vfs_state_qword(state_ptr, vfs_slot_desc_capacity())
    while desc_id <= capacity:
        slot = 0
        while slot < desc_slot_limit():
            set_vfs_desc_qword(state_ptr, desc_id, slot, 0)
            slot += 1
        desc_id += 1


def vfs_cstring_len(msg: cobj):
    i = 0
    while msg[i] != byte(0):
        i += 1
    return i


def vfs_path_equals(name_ptr: int, name_len: int, path_ptr: int, path_len: int):
    if name_len != path_len:
        return False

    i = 0
    while i < name_len:
        if byte(load_byte_region(name_ptr, name_len, i)) != byte(load_byte_region(path_ptr, path_len, i)):
            return False
        i += 1
    return True


def vfs_path_equals_cstring(name_ptr: int, name_len: int, path: cobj):
    if name_len != vfs_cstring_len(path):
        return False

    i = 0
    while i < name_len:
        if byte(load_byte_region(name_ptr, name_len, i)) != path[i]:
            return False
        i += 1
    return True


def vfs_path_has_prefix(name_ptr: int, name_len: int, prefix_ptr: int, prefix_len: int):
    i = 0
    if prefix_len > name_len:
        return False
    while i < prefix_len:
        if byte(load_byte_region(name_ptr, name_len, i)) != byte(load_byte_region(prefix_ptr, prefix_len, i)):
            return False
        i += 1
    return True


def vfs_normalize_path(path_ptr: int, path_len: int):
    src_index = 0
    out_len = 0
    component_start = 0
    out_ptr = 0

    if path_ptr == 0 or path_len <= 0:
        return 0, 0
    if byte(load_byte_region(path_ptr, path_len, 0)) != byte(47):
        return 0, 0

    out_ptr = alloc_bytes(path_len + 2)
    store_byte(out_ptr + 0, 47)
    out_len = 1
    src_index = 1

    while src_index < path_len:
        while src_index < path_len and byte(load_byte_region(path_ptr, path_len, src_index)) == byte(47):
            src_index += 1
        if src_index >= path_len:
            break

        component_start = src_index
        while src_index < path_len and byte(load_byte_region(path_ptr, path_len, src_index)) != byte(47):
            src_index += 1

        component_len = src_index - component_start
        if component_len == 1 and byte(load_byte_region(path_ptr, path_len, component_start)) == byte(46):
            continue
        if component_len == 2 and byte(load_byte_region(path_ptr, path_len, component_start)) == byte(46) and byte(load_byte_region(path_ptr, path_len, component_start + 1)) == byte(46):
            if out_len > 1:
                out_len -= 1
                while out_len > 1 and load_byte(out_ptr + out_len - 1) != 47:
                    out_len -= 1
            continue

        if out_len > 1:
            store_byte(out_ptr + out_len, 47)
            out_len += 1

        component_index = 0
        while component_index < component_len:
            store_byte(out_ptr + out_len, load_byte(path_ptr + component_start + component_index))
            out_len += 1
            component_index += 1

    if out_len == 0:
        store_byte(out_ptr + 0, 47)
        out_len = 1
    store_byte(out_ptr + out_len, 0)
    return out_ptr, out_len


def vfs_set_node_name_data(state_ptr: int, node_id: int, name_ptr: int, name_len: int, data_ptr: int, data_len: int):
    set_vfs_node_qword(state_ptr, node_id, node_slot_name_ptr(), name_ptr)
    set_vfs_node_qword(state_ptr, node_id, node_slot_name_len(), name_len)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_ptr(), data_ptr)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_len(), data_len)


def vfs_set_node_meta(state_ptr: int, node_id: int, kind: int, flags: int, data_capacity: int):
    set_vfs_node_qword(state_ptr, node_id, node_slot_kind(), kind)
    set_vfs_node_qword(state_ptr, node_id, node_slot_flags(), flags)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_capacity(), data_capacity)


def vfs_reserve_node(state_ptr: int):
    node_id = vfs_state_qword(state_ptr, vfs_slot_node_count())
    if node_id >= max_vfs_nodes():
        panic("vfs node table full".c_str())
    set_vfs_state_qword(state_ptr, vfs_slot_node_count(), node_id + 1)
    return node_id


def vfs_copy_initramfs_slice(base_ptr: int, offset: int, length: int, nul_terminate: bool):
    dst_len = length
    dst = 0
    i = 0

    if nul_terminate:
        dst_len += 1
    dst = alloc_bytes(dst_len)
    while i < length:
        store_byte(dst + i, load_byte(base_ptr + offset + i))
        i += 1
    if nul_terminate:
        store_byte(dst + length, 0)
    return dst


def init_vfs(boot_info_ptr: int):
    initramfs_ptr = boot_info_qword(boot_info_ptr, 21)
    initramfs_size = boot_info_qword(boot_info_ptr, 22)
    state_ptr = alloc_bytes(vfs_slot_limit() * 8)
    node_table_ptr = alloc_bytes(max_vfs_nodes() * node_slot_limit() * 8)
    desc_table_ptr = alloc_bytes(max_vfs_descriptors() * desc_slot_limit() * 8)
    node_count = 0

    set_vfs_state_qword(state_ptr, vfs_slot_initramfs_ptr(), initramfs_ptr)
    set_vfs_state_qword(state_ptr, vfs_slot_initramfs_size(), initramfs_size)
    set_vfs_state_qword(state_ptr, vfs_slot_node_table_ptr(), node_table_ptr)
    set_vfs_state_qword(state_ptr, vfs_slot_node_count(), 0)
    set_vfs_state_qword(state_ptr, vfs_slot_desc_table_ptr(), desc_table_ptr)
    set_vfs_state_qword(state_ptr, vfs_slot_desc_capacity(), max_vfs_descriptors())
    vfs_clear_descriptors(state_ptr)

    if initramfs_ptr == 0 or initramfs_size == 0:
        return state_ptr

    if initramfs_size < 32:
        panic("initramfs too small".c_str())
    if vfs_raw_qword(initramfs_ptr + 0) != initramfs_magic():
        panic("initramfs magic mismatch".c_str())
    if vfs_raw_qword(initramfs_ptr + 8) != initramfs_version():
        panic("initramfs version mismatch".c_str())

    node_count = vfs_raw_qword(initramfs_ptr + 16)
    if node_count > max_vfs_nodes():
        panic("initramfs node count too large".c_str())

    entry_index = 0
    while entry_index < node_count:
        entry_ptr = initramfs_ptr + 32 + entry_index * 32
        name_off = vfs_raw_qword(entry_ptr + 0)
        name_len = vfs_raw_qword(entry_ptr + 8)
        data_off = vfs_raw_qword(entry_ptr + 16)
        data_len = vfs_raw_qword(entry_ptr + 24)

        if name_off + name_len > initramfs_size:
            panic("initramfs name range invalid".c_str())
        if data_off + data_len > initramfs_size:
            panic("initramfs data range invalid".c_str())

        vfs_set_node_name_data(state_ptr,
                               entry_index,
                               vfs_copy_initramfs_slice(initramfs_ptr, name_off, name_len, True),
                               name_len,
                               vfs_copy_initramfs_slice(initramfs_ptr, data_off, data_len, False),
                               data_len)
        vfs_set_node_meta(state_ptr,
                          entry_index,
                          vfs_node_kind_file(),
                          0,
                          data_len)
        entry_index += 1

    set_vfs_state_qword(state_ptr, vfs_slot_node_count(), node_count)
    tmp_dir_name = alloc_bytes(5)
    store_byte(tmp_dir_name + 0, 47)
    store_byte(tmp_dir_name + 1, 116)
    store_byte(tmp_dir_name + 2, 109)
    store_byte(tmp_dir_name + 3, 112)
    store_byte(tmp_dir_name + 4, 0)
    tmp_dir_id = vfs_reserve_node(state_ptr)
    vfs_set_node_name_data(state_ptr, tmp_dir_id, tmp_dir_name, 4, 0, 0)
    vfs_set_node_meta(state_ptr, tmp_dir_id, vfs_node_kind_directory(), node_flag_writable(), 0)
    return state_ptr


def dump_vfs_summary(state_ptr: int):
    console_write_label_hex("initramfs.ptr=".c_str(), vfs_state_qword(state_ptr, vfs_slot_initramfs_ptr()))
    console_write_label_u64("initramfs.size=".c_str(), vfs_state_qword(state_ptr, vfs_slot_initramfs_size()))
    console_write_label_u64("vfs.files=".c_str(), vfs_state_qword(state_ptr, vfs_slot_node_count()))


def vfs_lookup_path(state_ptr: int, path_ptr: int, path_len: int):
    node_id = 0
    node_count = vfs_state_qword(state_ptr, vfs_slot_node_count())
    while node_id < node_count:
        if vfs_path_equals(vfs_node_qword(state_ptr, node_id, node_slot_name_ptr()),
                           vfs_node_qword(state_ptr, node_id, node_slot_name_len()),
                           path_ptr,
                           path_len):
            return node_id
        node_id += 1
    return -1


def vfs_lookup_cstring(state_ptr: int, path: cobj):
    node_id = 0
    node_count = vfs_state_qword(state_ptr, vfs_slot_node_count())
    while node_id < node_count:
        if vfs_path_equals_cstring(vfs_node_qword(state_ptr, node_id, node_slot_name_ptr()),
                                   vfs_node_qword(state_ptr, node_id, node_slot_name_len()),
                                   path):
            return node_id
        node_id += 1
    return -1


def vfs_alloc_descriptor(state_ptr: int, kind: int, flags: int, node_id: int, offset: int):
    desc_id = 1
    capacity = vfs_state_qword(state_ptr, vfs_slot_desc_capacity())
    while desc_id <= capacity:
        if vfs_desc_qword(state_ptr, desc_id, desc_slot_kind()) == desc_kind_closed():
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_kind(), kind)
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_flags(), flags)
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_node_id(), node_id)
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_offset(), offset)
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_path_ptr(), 0)
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_path_len(), 0)
            return desc_id
        desc_id += 1
    return 0


def vfs_alloc_console_in_descriptor(state_ptr: int):
    return vfs_alloc_descriptor(state_ptr, desc_kind_console_in(), 0, 0, 0)


def vfs_alloc_console_out_descriptor(state_ptr: int):
    return vfs_alloc_descriptor(state_ptr, desc_kind_console_out(), 0, 0, 0)


def vfs_alloc_directory_descriptor(state_ptr: int, path_ptr: int, path_len: int, offset: int):
    desc_id = vfs_alloc_descriptor(state_ptr, desc_kind_directory(), 0, 0, offset)
    if desc_id != 0:
        set_vfs_desc_qword(state_ptr, desc_id, desc_slot_path_ptr(), path_ptr)
        set_vfs_desc_qword(state_ptr, desc_id, desc_slot_path_len(), path_len)
    return desc_id


def vfs_node_matches_directory(state_ptr: int, node_id: int, dir_ptr: int, dir_len: int):
    name_ptr = vfs_node_qword(state_ptr, node_id, node_slot_name_ptr())
    name_len = vfs_node_qword(state_ptr, node_id, node_slot_name_len())

    if dir_len == 1:
        return name_len > 1 and byte(load_byte_region(name_ptr, name_len, 0)) == byte(47)
    if name_len <= dir_len:
        return False
    if not vfs_path_has_prefix(name_ptr, name_len, dir_ptr, dir_len):
        return False
    return byte(load_byte_region(name_ptr, name_len, dir_len)) == byte(47)


def vfs_directory_exists(state_ptr: int, dir_ptr: int, dir_len: int):
    node_id = 0
    node_count = vfs_state_qword(state_ptr, vfs_slot_node_count())
    if dir_len == 1 and byte(load_byte_region(dir_ptr, dir_len, 0)) == byte(47):
        return True
    while node_id < node_count:
        if vfs_node_qword(state_ptr, node_id, node_slot_kind()) == vfs_node_kind_directory():
            if vfs_path_equals(vfs_node_qword(state_ptr, node_id, node_slot_name_ptr()),
                               vfs_node_qword(state_ptr, node_id, node_slot_name_len()),
                               dir_ptr,
                               dir_len):
                return True
        if vfs_node_matches_directory(state_ptr, node_id, dir_ptr, dir_len):
            return True
        node_id += 1
    return False


def vfs_path_parent(path_ptr: int, path_len: int):
    index = path_len - 1
    parent_len = 0
    parent_ptr = 0
    if path_len <= 1:
        return 0, 0
    while index > 0 and byte(load_byte_region(path_ptr, path_len, index)) != byte(47):
        index -= 1
    if index == 0:
        parent_ptr = alloc_bytes(2)
        store_byte(parent_ptr + 0, 47)
        store_byte(parent_ptr + 1, 0)
        return parent_ptr, 1
    parent_len = index
    parent_ptr = alloc_bytes(parent_len + 1)
    index = 0
    while index < parent_len:
        store_byte(parent_ptr + index, load_byte_region(path_ptr, path_len, index))
        index += 1
    store_byte(parent_ptr + parent_len, 0)
    return parent_ptr, parent_len


def vfs_create_tmpfs_file(state_ptr: int, path_ptr: int, path_len: int):
    parent_ptr = 0
    parent_len = 0
    parent_id = -1
    parent_ptr, parent_len = vfs_path_parent(path_ptr, path_len)
    if parent_ptr == 0 or parent_len <= 0:
        return -1
    parent_id = vfs_lookup_path(state_ptr, parent_ptr, parent_len)
    if parent_id < 0:
        return -1
    if vfs_node_qword(state_ptr, parent_id, node_slot_kind()) != vfs_node_kind_directory():
        return -1
    if (vfs_node_qword(state_ptr, parent_id, node_slot_flags()) & node_flag_writable()) == 0:
        return -1
    node_id = vfs_reserve_node(state_ptr)
    vfs_set_node_name_data(state_ptr, node_id, path_ptr, path_len, 0, 0)
    vfs_set_node_meta(state_ptr, node_id, vfs_node_kind_file(), node_flag_writable(), 0)
    return node_id


def vfs_grow_node_data(state_ptr: int, node_id: int, min_capacity: int):
    data_ptr = vfs_node_qword(state_ptr, node_id, node_slot_data_ptr())
    data_len = vfs_node_qword(state_ptr, node_id, node_slot_data_len())
    data_capacity = vfs_node_qword(state_ptr, node_id, node_slot_data_capacity())
    new_ptr = 0
    copied = 0
    if min_capacity <= data_capacity:
        return data_ptr
    if min_capacity < 64:
        min_capacity = 64
    if data_capacity != 0 and min_capacity < data_capacity * 2:
        min_capacity = data_capacity * 2
    new_ptr = alloc_bytes(min_capacity)
    while copied < data_len:
        store_byte(new_ptr + copied, load_byte(data_ptr + copied))
        copied += 1
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_ptr(), new_ptr)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_capacity(), min_capacity)
    return new_ptr


def vfs_directory_child_component(state_ptr: int, node_id: int, dir_ptr: int, dir_len: int):
    name_ptr = vfs_node_qword(state_ptr, node_id, node_slot_name_ptr())
    name_len = vfs_node_qword(state_ptr, node_id, node_slot_name_len())
    start = 1
    end = 1

    if not vfs_node_matches_directory(state_ptr, node_id, dir_ptr, dir_len):
        return 0, 0

    if dir_len == 1:
        start = 1
    else:
        start = dir_len + 1
    end = start

    while end < name_len and byte(load_byte_region(name_ptr, name_len, end)) != byte(47):
        end += 1
    return name_ptr + start, end - start


def vfs_directory_child_seen_before(state_ptr: int, dir_ptr: int, dir_len: int, node_id: int, child_ptr: int, child_len: int):
    scan = 0
    while scan < node_id:
        other_ptr = 0
        other_len = 0
        other_ptr, other_len = vfs_directory_child_component(state_ptr, scan, dir_ptr, dir_len)
        if other_len == child_len and other_len != 0 and vfs_path_equals(other_ptr, other_len, child_ptr, child_len):
            return True
        scan += 1
    return False


def vfs_directory_child_count(state_ptr: int, dir_ptr: int, dir_len: int):
    node_id = 0
    node_count = vfs_state_qword(state_ptr, vfs_slot_node_count())
    count = 0

    while node_id < node_count:
        child_ptr = 0
        child_len = 0
        child_ptr, child_len = vfs_directory_child_component(state_ptr, node_id, dir_ptr, dir_len)
        if child_len != 0 and not vfs_directory_child_seen_before(state_ptr, dir_ptr, dir_len, node_id, child_ptr, child_len):
            count += 1
        node_id += 1
    return count


def vfs_open_path(state_ptr: int, path_ptr: int, path_len: int, flags: int):
    normalized_ptr = 0
    normalized_len = 0
    node_id = -1

    if (flags & ~3) != 0:
        return 0
    if path_ptr == 0 or path_len <= 0:
        return 0

    normalized_ptr, normalized_len = vfs_normalize_path(path_ptr, path_len)
    if normalized_ptr == 0 or normalized_len <= 0:
        return 0
    if normalized_len == 1 and byte(load_byte_region(normalized_ptr, normalized_len, 0)) == byte(47):
        return vfs_alloc_directory_descriptor(state_ptr, normalized_ptr, normalized_len, 0)

    node_id = vfs_lookup_path(state_ptr, normalized_ptr, normalized_len)
    if node_id < 0:
        if (flags & 1) != 0:
            node_id = vfs_create_tmpfs_file(state_ptr, normalized_ptr, normalized_len)
        if node_id >= 0:
            return vfs_alloc_descriptor(state_ptr, desc_kind_initramfs_file(), flags, node_id, 0)
        if vfs_directory_exists(state_ptr, normalized_ptr, normalized_len):
            return vfs_alloc_directory_descriptor(state_ptr, normalized_ptr, normalized_len, 0)
        return 0
    if vfs_node_qword(state_ptr, node_id, node_slot_kind()) == vfs_node_kind_directory():
        return vfs_alloc_directory_descriptor(state_ptr, normalized_ptr, normalized_len, 0)
    if (flags & 2) != 0 and (vfs_node_qword(state_ptr, node_id, node_slot_flags()) & node_flag_writable()) != 0:
        set_vfs_node_qword(state_ptr, node_id, node_slot_data_len(), 0)
    return vfs_alloc_descriptor(state_ptr, desc_kind_initramfs_file(), flags, node_id, 0)


def vfs_open_cstring(state_ptr: int, path: cobj):
    path_len = vfs_cstring_len(path)
    path_buf = alloc_bytes(path_len + 1)
    i = 0
    while i < path_len:
        store_byte(path_buf + i, int(path[i]))
        i += 1
    store_byte(path_buf + path_len, 0)
    return vfs_open_path(state_ptr, path_buf, path_len, 0)


def vfs_close_descriptor(state_ptr: int, desc_id: int):
    if desc_id <= 0:
        return -1
    if vfs_desc_qword(state_ptr, desc_id, desc_slot_kind()) == desc_kind_closed():
        return -1

    slot = 0
    while slot < desc_slot_limit():
        set_vfs_desc_qword(state_ptr, desc_id, slot, 0)
        slot += 1
    return 0


def vfs_write_descriptor(state_ptr: int, desc_id: int, ptr: int, length: int):
    if desc_id <= 0:
        return -1
    if length < 0:
        return -1

    kind = vfs_desc_qword(state_ptr, desc_id, desc_slot_kind())
    if kind == desc_kind_console_out():
        return console_write_ptr_len(ptr, length)
    if kind != desc_kind_initramfs_file():
        return -1
    node_id = vfs_desc_qword(state_ptr, desc_id, desc_slot_node_id())
    if (vfs_node_qword(state_ptr, node_id, node_slot_flags()) & node_flag_writable()) == 0:
        return -1
    offset = vfs_desc_qword(state_ptr, desc_id, desc_slot_offset())
    if offset + length < offset:
        return -1
    data_ptr = vfs_grow_node_data(state_ptr, node_id, offset + length)
    copied = 0
    while copied < length:
        store_byte(data_ptr + offset + copied, load_byte(ptr + copied))
        copied += 1
    if offset + length > vfs_node_qword(state_ptr, node_id, node_slot_data_len()):
        set_vfs_node_qword(state_ptr, node_id, node_slot_data_len(), offset + length)
    set_vfs_desc_qword(state_ptr, desc_id, desc_slot_offset(), offset + length)
    return length


def vfs_stat_descriptor(state_ptr: int, desc_id: int, dst_ptr: int):
    if desc_id <= 0 or dst_ptr == 0:
        return -1

    kind = vfs_desc_qword(state_ptr, desc_id, desc_slot_kind())
    if kind == desc_kind_closed():
        return -1
    if kind == desc_kind_directory():
        dir_ptr = vfs_desc_qword(state_ptr, desc_id, desc_slot_path_ptr())
        dir_len = vfs_desc_qword(state_ptr, desc_id, desc_slot_path_len())
        store_qword_region(dst_ptr, 2, 0, vfs_node_kind_directory())
        store_qword_region(dst_ptr, 2, 1, vfs_directory_child_count(state_ptr, dir_ptr, dir_len))
        return 0
    if kind == desc_kind_initramfs_file():
        node_id = vfs_desc_qword(state_ptr, desc_id, desc_slot_node_id())
        store_qword_region(dst_ptr, 2, 0, vfs_node_qword(state_ptr, node_id, node_slot_kind()))
        store_qword_region(dst_ptr, 2, 1, vfs_node_qword(state_ptr, node_id, node_slot_data_len()))
        return 0
    return -1


def vfs_readdir_descriptor(state_ptr: int, desc_id: int, dst_ptr: int, length: int):
    if desc_id <= 0:
        return -1
    if length < 0:
        return -1
    if dst_ptr == 0 and length != 0:
        return -1

    kind = vfs_desc_qword(state_ptr, desc_id, desc_slot_kind())
    if kind != desc_kind_directory():
        return -1

    index = vfs_desc_qword(state_ptr, desc_id, desc_slot_offset())
    dir_ptr = vfs_desc_qword(state_ptr, desc_id, desc_slot_path_ptr())
    dir_len = vfs_desc_qword(state_ptr, desc_id, desc_slot_path_len())
    node_count = vfs_state_qword(state_ptr, vfs_slot_node_count())
    copied = 0

    while index < node_count:
        child_ptr = 0
        child_len = 0
        child_ptr, child_len = vfs_directory_child_component(state_ptr, index, dir_ptr, dir_len)
        if child_len != 0 and not vfs_directory_child_seen_before(state_ptr, dir_ptr, dir_len, index, child_ptr, child_len):
            if length > child_len:
                length = child_len
            while copied < length:
                store_byte(dst_ptr + copied, load_byte(child_ptr + copied))
                copied += 1
            set_vfs_desc_qword(state_ptr, desc_id, desc_slot_offset(), index + 1)
            return copied
        index += 1
    return 0


def vfs_read_descriptor(state_ptr: int, desc_id: int, dst_ptr: int, length: int):
    if desc_id <= 0:
        return -1
    if length < 0:
        return -1
    if dst_ptr == 0 and length != 0:
        return -1

    kind = vfs_desc_qword(state_ptr, desc_id, desc_slot_kind())
    if kind == desc_kind_console_in():
        return console_read_ptr_len(dst_ptr, length)
    if kind == desc_kind_directory():
        return -1
    if kind != desc_kind_initramfs_file():
        return -1

    node_id = vfs_desc_qword(state_ptr, desc_id, desc_slot_node_id())
    offset = vfs_desc_qword(state_ptr, desc_id, desc_slot_offset())
    data_ptr = vfs_node_qword(state_ptr, node_id, node_slot_data_ptr())
    data_len = vfs_node_qword(state_ptr, node_id, node_slot_data_len())
    remaining = data_len - offset
    copied = 0
    if remaining <= 0:
        return 0
    if length > remaining:
        length = remaining

    while copied < length:
        store_byte(dst_ptr + copied, load_byte(data_ptr + offset + copied))
        copied += 1

    set_vfs_desc_qword(state_ptr, desc_id, desc_slot_offset(), offset + copied)
    return copied


def vfs_self_test(state_ptr: int):
    path = alloc_bytes(16)
    nested_path = alloc_bytes(24)
    tmp_path = alloc_bytes(20)
    tmp_dir_path = alloc_bytes(8)
    tmp_msg = alloc_bytes(16)
    desc = 0
    dir_desc = 0
    subdir_desc = 0
    tmp_desc = 0
    tmp_dir_desc = 0
    buf = 0
    count = 0
    stat_buf = 0

    store_byte(path + 0, 47)
    store_byte(path + 1, 104)
    store_byte(path + 2, 101)
    store_byte(path + 3, 108)
    store_byte(path + 4, 108)
    store_byte(path + 5, 111)
    store_byte(path + 6, 46)
    store_byte(path + 7, 116)
    store_byte(path + 8, 120)
    store_byte(path + 9, 116)
    store_byte(path + 10, 0)
    store_byte(nested_path + 0, 47)
    store_byte(nested_path + 1, 47)
    store_byte(nested_path + 2, 98)
    store_byte(nested_path + 3, 105)
    store_byte(nested_path + 4, 110)
    store_byte(nested_path + 5, 47)
    store_byte(nested_path + 6, 46)
    store_byte(nested_path + 7, 47)
    store_byte(nested_path + 8, 104)
    store_byte(nested_path + 9, 101)
    store_byte(nested_path + 10, 108)
    store_byte(nested_path + 11, 108)
    store_byte(nested_path + 12, 111)
    store_byte(nested_path + 13, 0)
    store_byte(tmp_path + 0, 47)
    store_byte(tmp_path + 1, 116)
    store_byte(tmp_path + 2, 109)
    store_byte(tmp_path + 3, 112)
    store_byte(tmp_path + 4, 47)
    store_byte(tmp_path + 5, 108)
    store_byte(tmp_path + 6, 111)
    store_byte(tmp_path + 7, 103)
    store_byte(tmp_path + 8, 46)
    store_byte(tmp_path + 9, 116)
    store_byte(tmp_path + 10, 120)
    store_byte(tmp_path + 11, 116)
    store_byte(tmp_path + 12, 0)
    store_byte(tmp_dir_path + 0, 47)
    store_byte(tmp_dir_path + 1, 116)
    store_byte(tmp_dir_path + 2, 109)
    store_byte(tmp_dir_path + 3, 112)
    store_byte(tmp_dir_path + 4, 0)
    store_byte(tmp_msg + 0, 116)
    store_byte(tmp_msg + 1, 109)
    store_byte(tmp_msg + 2, 112)
    store_byte(tmp_msg + 3, 102)
    store_byte(tmp_msg + 4, 115)
    store_byte(tmp_msg + 5, 45)
    store_byte(tmp_msg + 6, 111)
    store_byte(tmp_msg + 7, 107)
    store_byte(tmp_msg + 8, 0)
    desc = vfs_open_path(state_ptr, path, 10, 0)
    if desc == 0:
        panic("vfs self-test open failed".c_str())

    buf = alloc_bytes(64)
    count = vfs_read_descriptor(state_ptr, desc, buf, 64)
    if count <= 0:
        panic("vfs self-test read failed".c_str())
    stat_buf = alloc_bytes(16)
    if vfs_stat_descriptor(state_ptr, desc, stat_buf) != 0:
        panic("vfs self-test stat failed".c_str())
    dir_desc = vfs_open_cstring(state_ptr, "/".c_str())
    if dir_desc == 0:
        panic("vfs self-test dir open failed".c_str())
    subdir_desc = vfs_open_cstring(state_ptr, "/bin".c_str())
    if subdir_desc == 0:
        panic("vfs self-test subdir open failed".c_str())
    if vfs_open_path(state_ptr, nested_path, 13, 0) == 0:
        panic("vfs self-test nested path failed".c_str())
    tmp_desc = vfs_open_path(state_ptr, tmp_path, 12, 3)
    if tmp_desc == 0:
        panic("vfs self-test tmp create failed".c_str())
    if vfs_write_descriptor(state_ptr, tmp_desc, tmp_msg, 8) != 8:
        panic("vfs self-test tmp write failed".c_str())
    if vfs_close_descriptor(state_ptr, tmp_desc) != 0:
        panic("vfs self-test tmp close failed".c_str())
    tmp_desc = vfs_open_path(state_ptr, tmp_path, 12, 0)
    if tmp_desc == 0:
        panic("vfs self-test tmp reopen failed".c_str())
    tmp_dir_desc = vfs_open_path(state_ptr, tmp_dir_path, 4, 0)
    if tmp_dir_desc == 0:
        panic("vfs self-test tmp dir open failed".c_str())

    console_write_label_u64("vfs.self_test.bytes=".c_str(), count)
    console_write_label_u64("vfs.self_test.kind=".c_str(), load_qword_region(stat_buf, 2, 0))
    console_write_label_u64("vfs.self_test.size=".c_str(), load_qword_region(stat_buf, 2, 1))
    console_write("vfs.self_test.sample=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    count = vfs_readdir_descriptor(state_ptr, dir_desc, buf, 64)
    if count <= 0:
        panic("vfs self-test readdir failed".c_str())
    console_write("vfs.self_test.dirent=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    count = vfs_readdir_descriptor(state_ptr, subdir_desc, buf, 64)
    if count <= 0:
        panic("vfs self-test subdir readdir failed".c_str())
    console_write("vfs.self_test.subdir=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    count = vfs_read_descriptor(state_ptr, tmp_desc, buf, 64)
    if count != 8:
        panic("vfs self-test tmp read failed".c_str())
    console_write("vfs.self_test.tmp=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    count = vfs_readdir_descriptor(state_ptr, tmp_dir_desc, buf, 64)
    if count <= 0:
        panic("vfs self-test tmp dir readdir failed".c_str())
    console_write("vfs.self_test.tmpdir=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    if vfs_close_descriptor(state_ptr, desc) != 0:
        panic("vfs self-test close failed".c_str())
    if vfs_close_descriptor(state_ptr, dir_desc) != 0:
        panic("vfs self-test dir close failed".c_str())
    if vfs_close_descriptor(state_ptr, subdir_desc) != 0:
        panic("vfs self-test subdir close failed".c_str())
    if vfs_close_descriptor(state_ptr, tmp_desc) != 0:
        panic("vfs self-test tmp final close failed".c_str())
    if vfs_close_descriptor(state_ptr, tmp_dir_desc) != 0:
        panic("vfs self-test tmp dir close failed".c_str())
    console_write_line("vfs self-test ok".c_str())

from kboot import boot_info_qword
from kconsole import console_write
from kconsole import console_write_label_hex
from kconsole import console_write_label_u64
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


def node_slot_limit():
    return 4


def desc_slot_kind():
    return 0


def desc_slot_flags():
    return 1


def desc_slot_node_id():
    return 2


def desc_slot_offset():
    return 3


def desc_slot_limit():
    return 4


def desc_kind_closed():
    return 0


def desc_kind_console_in():
    return 1


def desc_kind_console_out():
    return 2


def desc_kind_initramfs_file():
    return 3


def max_vfs_nodes():
    return 16


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


def vfs_set_node(state_ptr: int, node_id: int, name_ptr: int, name_len: int, data_ptr: int, data_len: int):
    set_vfs_node_qword(state_ptr, node_id, node_slot_name_ptr(), name_ptr)
    set_vfs_node_qword(state_ptr, node_id, node_slot_name_len(), name_len)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_ptr(), data_ptr)
    set_vfs_node_qword(state_ptr, node_id, node_slot_data_len(), data_len)


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
        store_byte(dst + length, byte(0))
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

        vfs_set_node(state_ptr,
                     entry_index,
                     vfs_copy_initramfs_slice(initramfs_ptr, name_off, name_len, True),
                     name_len,
                     vfs_copy_initramfs_slice(initramfs_ptr, data_off, data_len, False),
                     data_len)
        entry_index += 1

    set_vfs_state_qword(state_ptr, vfs_slot_node_count(), node_count)
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
            return desc_id
        desc_id += 1
    return 0


def vfs_alloc_console_in_descriptor(state_ptr: int):
    return vfs_alloc_descriptor(state_ptr, desc_kind_console_in(), 0, 0, 0)


def vfs_alloc_console_out_descriptor(state_ptr: int):
    return vfs_alloc_descriptor(state_ptr, desc_kind_console_out(), 0, 0, 0)


def vfs_open_path(state_ptr: int, path_ptr: int, path_len: int, flags: int):
    if flags != 0:
        return 0
    if path_ptr == 0 or path_len <= 0:
        return 0

    node_id = vfs_lookup_path(state_ptr, path_ptr, path_len)
    if node_id < 0:
        return 0
    return vfs_alloc_descriptor(state_ptr, desc_kind_initramfs_file(), flags, node_id, 0)


def vfs_open_cstring(state_ptr: int, path: cobj):
    node_id = vfs_lookup_cstring(state_ptr, path)
    if node_id < 0:
        return 0
    return vfs_alloc_descriptor(state_ptr, desc_kind_initramfs_file(), 0, node_id, 0)


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
    if kind != desc_kind_console_out():
        return -1
    return console_write_ptr_len(ptr, length)


def vfs_read_descriptor(state_ptr: int, desc_id: int, dst_ptr: int, length: int):
    if desc_id <= 0:
        return -1
    if length < 0:
        return -1
    if dst_ptr == 0 and length != 0:
        return -1

    kind = vfs_desc_qword(state_ptr, desc_id, desc_slot_kind())
    if kind == desc_kind_console_in():
        return 0
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
    desc = 0
    buf = 0
    count = 0

    store_byte(path + 0, byte(47))
    store_byte(path + 1, byte(104))
    store_byte(path + 2, byte(101))
    store_byte(path + 3, byte(108))
    store_byte(path + 4, byte(108))
    store_byte(path + 5, byte(111))
    store_byte(path + 6, byte(46))
    store_byte(path + 7, byte(116))
    store_byte(path + 8, byte(120))
    store_byte(path + 9, byte(116))
    store_byte(path + 10, byte(0))
    desc = vfs_open_path(state_ptr, path, 10, 0)
    if desc == 0:
        panic("vfs self-test open failed".c_str())

    buf = alloc_bytes(64)
    count = vfs_read_descriptor(state_ptr, desc, buf, 64)
    if count <= 0:
        panic("vfs self-test read failed".c_str())

    console_write_label_hex("vfs.node0.name.ptr=".c_str(), vfs_node_qword(state_ptr, 0, node_slot_name_ptr()))
    console_write_label_hex("vfs.node0.data.ptr=".c_str(), vfs_node_qword(state_ptr, 0, node_slot_data_ptr()))
    console_write_label_hex("vfs.node0.data.q0=".c_str(), vfs_raw_qword(vfs_node_qword(state_ptr, 0, node_slot_data_ptr())))
    console_write_label_hex("vfs.node0.data.q1=".c_str(), vfs_raw_qword(vfs_node_qword(state_ptr, 0, node_slot_data_ptr()) + 8))
    console_write("vfs.node0.name.sample=".c_str())
    console_write_ptr_len(vfs_node_qword(state_ptr, 0, node_slot_name_ptr()), vfs_node_qword(state_ptr, 0, node_slot_name_len()))
    console_write("\n".c_str())
    console_write("vfs.node0.data.sample=".c_str())
    console_write_ptr_len(vfs_node_qword(state_ptr, 0, node_slot_data_ptr()), vfs_node_qword(state_ptr, 0, node_slot_data_len()))
    console_write("\n".c_str())
    console_write_label_u64("vfs.self_test.bytes=".c_str(), count)
    console_write("vfs.self_test.sample=".c_str())
    console_write_ptr_len(buf, count)
    console_write("\n".c_str())
    if vfs_close_descriptor(state_ptr, desc) != 0:
        panic("vfs self-test close failed".c_str())
    console_write_line("vfs self-test ok".c_str())

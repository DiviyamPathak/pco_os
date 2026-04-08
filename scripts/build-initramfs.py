#!/usr/bin/env python3
import os
import struct
import sys


MAGIC = 0x31534652494F4350
VERSION = 1


def align_up(value: int, align: int):
    return (value + align - 1) & ~(align - 1)


def collect_files(root: str):
    entries = []
    for base, _dirs, files in os.walk(root):
        files.sort()
        for name in files:
            full = os.path.join(base, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            with open(full, "rb") as f:
                data = f.read()
            entries.append((("/" + rel).encode("utf-8"), data))
    entries.sort(key=lambda item: item[0])
    return entries


def build_image(entries):
    header_size = 32
    entry_size = 32
    table_size = len(entries) * entry_size
    blob = bytearray()
    blob.extend(struct.pack("<QQQQ", MAGIC, VERSION, len(entries), 0))
    blob.extend(b"\x00" * table_size)

    entry_bytes = []
    data_cursor = header_size + table_size
    for name, data in entries:
        aligned_cursor = align_up(data_cursor, 64)
        if aligned_cursor > len(blob):
            blob.extend(b"\x00" * (aligned_cursor - len(blob)))
        data_cursor = aligned_cursor
        name_off = data_cursor
        blob.extend(name)
        data_cursor += len(name)
        aligned_cursor = align_up(data_cursor, 64)
        if aligned_cursor > len(blob):
            blob.extend(b"\x00" * (aligned_cursor - len(blob)))
        data_cursor = aligned_cursor
        data_off = data_cursor
        blob.extend(data)
        data_cursor += len(data)
        entry_bytes.append(struct.pack("<QQQQ", name_off, len(name), data_off, len(data)))

    for i, packed in enumerate(entry_bytes):
        start = header_size + i * entry_size
        blob[start:start + entry_size] = packed
    return bytes(blob)


def main():
    if len(sys.argv) != 3:
        print("usage: build-initramfs.py <input-dir> <output-file>", file=sys.stderr)
        return 1

    src_dir = sys.argv[1]
    out_file = sys.argv[2]
    entries = collect_files(src_dir)
    image = build_image(entries)

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "wb") as f:
        f.write(image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

typedef unsigned long long UINT64;
typedef unsigned int UINT32;
typedef unsigned short UINT16;
typedef unsigned char UINT8;
typedef signed short INT16;
typedef unsigned long UINTN;
typedef void VOID;
typedef UINT64 EFI_STATUS;
typedef VOID *EFI_HANDLE;
typedef VOID *EFI_EVENT;
typedef UINT64 EFI_PHYSICAL_ADDRESS;
typedef UINT64 EFI_LBA;
typedef UINT16 CHAR16;

#define EFIAPI __attribute__((ms_abi))
#define NULL ((VOID *)0)

#define EFI_SUCCESS 0
#define EFI_LOAD_ERROR 0x8000000000000001ULL
#define EFI_INVALID_PARAMETER 0x8000000000000002ULL
#define EFI_BUFFER_TOO_SMALL 0x8000000000000005ULL
#define EFI_NOT_FOUND 0x800000000000000EULL
#define EFI_ERROR(x) (((x) >> 63) != 0)

#define AllocateAnyPages 0
#define AllocateAddress 2
#define EfiLoaderData 2

#define EFI_FILE_MODE_READ 0x0000000000000001ULL

#define PT_LOAD 1

#define BOOT_INFO_MAGIC 0x50434F424F4F5431ULL
#define BOOTMETA_MAGIC 0x50434F4D45544131ULL

typedef struct {
    UINT32 Data1;
    UINT16 Data2;
    UINT16 Data3;
    UINT8 Data4[8];
} EFI_GUID;

typedef struct {
    UINT64 Signature[21];
} BOOT_INFO_BLOCK;

typedef struct {
    UINT64 Base;
    UINT64 Length;
    UINT64 Type;
    UINT64 Attrs;
} MEMORY_REGION;

typedef struct {
    UINT64 Magic;
    UINT64 Version;
    UINT64 Entry64;
} KERNEL_BOOTMETA;

typedef struct {
    UINT64 Signature;
    UINT32 Revision;
    UINT32 HeaderSize;
    UINT32 CRC32;
    UINT32 Reserved;
} EFI_TABLE_HEADER;

typedef struct {
    UINT16 Year;
    UINT8 Month;
    UINT8 Day;
    UINT8 Hour;
    UINT8 Minute;
    UINT8 Second;
    UINT8 Pad1;
    UINT32 Nanosecond;
    INT16 TimeZone;
    UINT8 Daylight;
    UINT8 Pad2;
} EFI_TIME;

typedef struct {
    EFI_TABLE_HEADER Hdr;
    CHAR16 *FirmwareVendor;
    UINT32 FirmwareRevision;
    EFI_HANDLE ConsoleInHandle;
    VOID *ConIn;
    EFI_HANDLE ConsoleOutHandle;
    struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *ConOut;
    EFI_HANDLE StandardErrorHandle;
    VOID *StdErr;
    VOID *RuntimeServices;
    struct EFI_BOOT_SERVICES *BootServices;
    UINTN NumberOfTableEntries;
    VOID *ConfigurationTable;
} EFI_SYSTEM_TABLE;

typedef EFI_STATUS (EFIAPI *EFI_TEXT_RESET)(struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *, UINT8);
typedef EFI_STATUS (EFIAPI *EFI_TEXT_STRING)(struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *, CHAR16 *);

typedef struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL {
    EFI_TEXT_RESET Reset;
    EFI_TEXT_STRING OutputString;
    VOID *TestString;
    VOID *QueryMode;
    VOID *SetMode;
    VOID *SetAttribute;
    VOID *ClearScreen;
    VOID *SetCursorPosition;
    VOID *EnableCursor;
    VOID *Mode;
} EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL;

typedef struct {
    UINT32 Type;
    UINT32 Pad;
    EFI_PHYSICAL_ADDRESS PhysicalStart;
    EFI_PHYSICAL_ADDRESS VirtualStart;
    UINT64 NumberOfPages;
    UINT64 Attribute;
} EFI_MEMORY_DESCRIPTOR;

typedef EFI_STATUS (EFIAPI *EFI_ALLOCATE_PAGES)(UINTN, UINTN, UINTN, EFI_PHYSICAL_ADDRESS *);
typedef EFI_STATUS (EFIAPI *EFI_FREE_PAGES)(EFI_PHYSICAL_ADDRESS, UINTN);
typedef EFI_STATUS (EFIAPI *EFI_GET_MEMORY_MAP)(UINTN *, EFI_MEMORY_DESCRIPTOR *, UINTN *, UINTN *, UINT32 *);
typedef EFI_STATUS (EFIAPI *EFI_ALLOCATE_POOL)(UINTN, UINTN, VOID **);
typedef EFI_STATUS (EFIAPI *EFI_FREE_POOL)(VOID *);
typedef EFI_STATUS (EFIAPI *EFI_HANDLE_PROTOCOL)(EFI_HANDLE, EFI_GUID *, VOID **);
typedef EFI_STATUS (EFIAPI *EFI_EXIT_BOOT_SERVICES)(EFI_HANDLE, UINTN);

typedef struct EFI_BOOT_SERVICES {
    EFI_TABLE_HEADER Hdr;
    VOID *RaiseTPL;
    VOID *RestoreTPL;
    EFI_ALLOCATE_PAGES AllocatePages;
    EFI_FREE_PAGES FreePages;
    EFI_GET_MEMORY_MAP GetMemoryMap;
    EFI_ALLOCATE_POOL AllocatePool;
    EFI_FREE_POOL FreePool;
    VOID *CreateEvent;
    VOID *SetTimer;
    VOID *WaitForEvent;
    VOID *SignalEvent;
    VOID *CloseEvent;
    VOID *CheckEvent;
    VOID *InstallProtocolInterface;
    VOID *ReinstallProtocolInterface;
    VOID *UninstallProtocolInterface;
    EFI_HANDLE_PROTOCOL HandleProtocol;
    VOID *Reserved;
    VOID *RegisterProtocolNotify;
    VOID *LocateHandle;
    VOID *LocateDevicePath;
    VOID *InstallConfigurationTable;
    VOID *LoadImage;
    VOID *StartImage;
    VOID *Exit;
    VOID *UnloadImage;
    EFI_EXIT_BOOT_SERVICES ExitBootServices;
    VOID *GetNextMonotonicCount;
    VOID *Stall;
    VOID *SetWatchdogTimer;
    VOID *ConnectController;
    VOID *DisconnectController;
    VOID *OpenProtocol;
    VOID *CloseProtocol;
    VOID *OpenProtocolInformation;
    VOID *ProtocolsPerHandle;
    VOID *LocateHandleBuffer;
    VOID *LocateProtocol;
    VOID *InstallMultipleProtocolInterfaces;
    VOID *UninstallMultipleProtocolInterfaces;
    VOID *CalculateCrc32;
    VOID *CopyMem;
    VOID *SetMem;
    VOID *CreateEventEx;
} EFI_BOOT_SERVICES;

typedef struct EFI_FILE_PROTOCOL EFI_FILE_PROTOCOL;

typedef EFI_STATUS (EFIAPI *EFI_FILE_OPEN)(EFI_FILE_PROTOCOL *, EFI_FILE_PROTOCOL **, CHAR16 *, UINT64, UINT64);
typedef EFI_STATUS (EFIAPI *EFI_FILE_CLOSE)(EFI_FILE_PROTOCOL *);
typedef EFI_STATUS (EFIAPI *EFI_FILE_READ)(EFI_FILE_PROTOCOL *, UINTN *, VOID *);
typedef EFI_STATUS (EFIAPI *EFI_FILE_SET_POSITION)(EFI_FILE_PROTOCOL *, UINT64);
typedef EFI_STATUS (EFIAPI *EFI_FILE_GET_INFO)(EFI_FILE_PROTOCOL *, EFI_GUID *, UINTN *, VOID *);

struct EFI_FILE_PROTOCOL {
    UINT64 Revision;
    EFI_FILE_OPEN Open;
    EFI_FILE_CLOSE Close;
    VOID *Delete;
    EFI_FILE_READ Read;
    VOID *Write;
    VOID *GetPosition;
    EFI_FILE_SET_POSITION SetPosition;
    EFI_FILE_GET_INFO GetInfo;
    VOID *SetInfo;
    VOID *Flush;
    VOID *OpenEx;
    VOID *ReadEx;
    VOID *WriteEx;
    VOID *FlushEx;
};

typedef EFI_STATUS (EFIAPI *EFI_OPEN_VOLUME)(VOID *, EFI_FILE_PROTOCOL **);

typedef struct {
    UINT64 Revision;
    EFI_OPEN_VOLUME OpenVolume;
} EFI_SIMPLE_FILE_SYSTEM_PROTOCOL;

typedef struct {
    UINT32 Revision;
    EFI_HANDLE ParentHandle;
    EFI_SYSTEM_TABLE *SystemTable;
    EFI_HANDLE DeviceHandle;
    VOID *FilePath;
    VOID *Reserved;
    UINT32 LoadOptionsSize;
    VOID *LoadOptions;
    VOID *ImageBase;
    UINT64 ImageSize;
    UINTN ImageCodeType;
    UINTN ImageDataType;
    VOID *Unload;
} EFI_LOADED_IMAGE_PROTOCOL;

typedef struct {
    UINT64 Size;
    UINT64 FileSize;
    UINT64 PhysicalSize;
    EFI_TIME CreateTime;
    EFI_TIME LastAccessTime;
    EFI_TIME ModificationTime;
    UINT64 Attribute;
    CHAR16 FileName[1];
} EFI_FILE_INFO;

typedef struct {
    UINT8 e_ident[16];
    UINT16 e_type;
    UINT16 e_machine;
    UINT32 e_version;
    UINT64 e_entry;
    UINT64 e_phoff;
    UINT64 e_shoff;
    UINT32 e_flags;
    UINT16 e_ehsize;
    UINT16 e_phentsize;
    UINT16 e_phnum;
    UINT16 e_shentsize;
    UINT16 e_shnum;
    UINT16 e_shstrndx;
} Elf64_Ehdr;

typedef struct {
    UINT32 p_type;
    UINT32 p_flags;
    UINT64 p_offset;
    UINT64 p_vaddr;
    UINT64 p_paddr;
    UINT64 p_filesz;
    UINT64 p_memsz;
    UINT64 p_align;
} Elf64_Phdr;

typedef struct {
    UINT32 sh_name;
    UINT32 sh_type;
    UINT64 sh_flags;
    UINT64 sh_addr;
    UINT64 sh_offset;
    UINT64 sh_size;
    UINT32 sh_link;
    UINT32 sh_info;
    UINT64 sh_addralign;
    UINT64 sh_entsize;
} Elf64_Shdr;

static EFI_GUID gLoadedImageProtocolGuid = {
    0x5b1b31a1, 0x9562, 0x11d2,
    {0x8e, 0x3f, 0x00, 0xa0, 0xc9, 0x69, 0x72, 0x3b}
};

static EFI_GUID gSimpleFileSystemProtocolGuid = {
    0x964e5b22, 0x6459, 0x11d2,
    {0x8e, 0x39, 0x00, 0xa0, 0xc9, 0x69, 0x72, 0x3b}
};

static EFI_GUID gFileInfoGuid = {
    0x09576e92, 0x6d3f, 0x11d2,
    {0x8e, 0x39, 0x00, 0xa0, 0xc9, 0x69, 0x72, 0x3b}
};

static VOID mem_copy(VOID *dst, const VOID *src, UINTN size) {
    UINT8 *out = (UINT8 *)dst;
    const UINT8 *in = (const UINT8 *)src;
    UINTN i;

    for (i = 0; i < size; ++i) {
        out[i] = in[i];
    }
}

static VOID mem_set(VOID *dst, UINT8 value, UINTN size) {
    UINT8 *out = (UINT8 *)dst;
    UINTN i;

    for (i = 0; i < size; ++i) {
        out[i] = value;
    }
}

static int ascii_equal(const char *a, const char *b) {
    UINTN i = 0;

    while (a[i] != 0 && b[i] != 0) {
        if (a[i] != b[i]) {
            return 0;
        }
        ++i;
    }

    return a[i] == 0 && b[i] == 0;
}

static UINT64 align_down(UINT64 value, UINT64 align) {
    return value & ~(align - 1);
}

static UINT64 align_up(UINT64 value, UINT64 align) {
    return (value + align - 1) & ~(align - 1);
}

static EFI_STATUS efi_puts(EFI_SYSTEM_TABLE *system_table, CHAR16 *message) {
    if (system_table == NULL || system_table->ConOut == NULL || system_table->ConOut->OutputString == NULL) {
        return EFI_SUCCESS;
    }
    return system_table->ConOut->OutputString(system_table->ConOut, message);
}

static UINT64 current_apic_id(void) {
    UINT32 eax = 1;
    UINT32 ebx;
    UINT32 ecx;
    UINT32 edx;

    __asm__ volatile("cpuid"
                     : "+a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
                     :
                     : "cc");

    return (UINT64)((ebx >> 24) & 0xff);
}

static EFI_STATUS open_root(EFI_HANDLE image_handle, EFI_SYSTEM_TABLE *system_table, EFI_FILE_PROTOCOL **root) {
    EFI_STATUS status;
    EFI_LOADED_IMAGE_PROTOCOL *loaded_image;
    EFI_SIMPLE_FILE_SYSTEM_PROTOCOL *file_system;

    loaded_image = NULL;
    file_system = NULL;

    status = system_table->BootServices->HandleProtocol(image_handle, &gLoadedImageProtocolGuid, (VOID **)&loaded_image);
    if (EFI_ERROR(status)) {
        return status;
    }

    status = system_table->BootServices->HandleProtocol(loaded_image->DeviceHandle, &gSimpleFileSystemProtocolGuid, (VOID **)&file_system);
    if (EFI_ERROR(status)) {
        return status;
    }

    return file_system->OpenVolume(file_system, root);
}

static EFI_STATUS read_entire_file(EFI_SYSTEM_TABLE *system_table, EFI_FILE_PROTOCOL *root, CHAR16 *path, VOID **buffer, UINTN *buffer_size) {
    EFI_STATUS status;
    EFI_FILE_PROTOCOL *file;
    UINT8 info_buffer[512];
    UINTN info_size;
    EFI_FILE_INFO *info;
    UINTN read_size;

    file = NULL;
    info_size = sizeof(info_buffer);

    status = root->Open(root, &file, path, EFI_FILE_MODE_READ, 0);
    if (EFI_ERROR(status)) {
        return status;
    }

    status = file->GetInfo(file, &gFileInfoGuid, &info_size, info_buffer);
    if (EFI_ERROR(status)) {
        file->Close(file);
        return status;
    }

    info = (EFI_FILE_INFO *)info_buffer;
    *buffer_size = (UINTN)info->FileSize;
    if (*buffer_size == 0) {
        file->Close(file);
        return EFI_LOAD_ERROR;
    }

    status = system_table->BootServices->AllocatePool(EfiLoaderData, *buffer_size, buffer);
    if (EFI_ERROR(status)) {
        file->Close(file);
        return status;
    }

    status = file->SetPosition(file, 0);
    if (EFI_ERROR(status)) {
        file->Close(file);
        return status;
    }

    read_size = *buffer_size;
    status = file->Read(file, &read_size, *buffer);
    file->Close(file);
    if (EFI_ERROR(status) || read_size != *buffer_size) {
        return EFI_LOAD_ERROR;
    }

    return EFI_SUCCESS;
}

static EFI_STATUS find_bootmeta(VOID *kernel_file, UINTN kernel_file_size, UINT64 *entry64) {
    const UINT8 *file_bytes;
    const Elf64_Ehdr *ehdr;
    const Elf64_Shdr *section_headers;
    const Elf64_Shdr *shstrtab;
    const char *string_table;
    UINTN i;

    file_bytes = (const UINT8 *)kernel_file;
    ehdr = (const Elf64_Ehdr *)kernel_file;
    if (kernel_file_size < sizeof(Elf64_Ehdr)) {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_ident[0] != 0x7f || ehdr->e_ident[1] != 'E' || ehdr->e_ident[2] != 'L' || ehdr->e_ident[3] != 'F') {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_shentsize != sizeof(Elf64_Shdr) || ehdr->e_shnum == 0 || ehdr->e_shstrndx >= ehdr->e_shnum) {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_shoff + (UINT64)ehdr->e_shentsize * (UINT64)ehdr->e_shnum > kernel_file_size) {
        return EFI_LOAD_ERROR;
    }

    section_headers = (const Elf64_Shdr *)(file_bytes + ehdr->e_shoff);
    shstrtab = &section_headers[ehdr->e_shstrndx];
    if (shstrtab->sh_offset + shstrtab->sh_size > kernel_file_size) {
        return EFI_LOAD_ERROR;
    }

    string_table = (const char *)(file_bytes + shstrtab->sh_offset);
    for (i = 0; i < ehdr->e_shnum; ++i) {
        const Elf64_Shdr *section;
        const char *name;
        const KERNEL_BOOTMETA *bootmeta;

        section = &section_headers[i];
        if (section->sh_offset + section->sh_size > kernel_file_size) {
            return EFI_LOAD_ERROR;
        }

        name = string_table + section->sh_name;
        if (!ascii_equal(name, ".bootmeta")) {
            continue;
        }

        if (section->sh_size < sizeof(KERNEL_BOOTMETA)) {
            return EFI_LOAD_ERROR;
        }

        bootmeta = (const KERNEL_BOOTMETA *)(file_bytes + section->sh_offset);
        if (bootmeta->Magic != BOOTMETA_MAGIC || bootmeta->Version != 1) {
            return EFI_LOAD_ERROR;
        }

        *entry64 = bootmeta->Entry64;
        return EFI_SUCCESS;
    }

    return EFI_NOT_FOUND;
}

static EFI_STATUS load_kernel_image(EFI_SYSTEM_TABLE *system_table,
                                    VOID *kernel_file,
                                    UINTN kernel_file_size,
                                    UINT64 *entry64,
                                    UINT64 *kernel_phys_base,
                                    UINT64 *kernel_phys_end) {
    const UINT8 *file_bytes;
    const Elf64_Ehdr *ehdr;
    const Elf64_Phdr *program_headers;
    UINT64 image_base;
    UINT64 image_end;
    UINTN i;
    EFI_PHYSICAL_ADDRESS image_addr;
    EFI_STATUS status;

    file_bytes = (const UINT8 *)kernel_file;
    ehdr = (const Elf64_Ehdr *)kernel_file;
    if (kernel_file_size < sizeof(Elf64_Ehdr)) {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_ident[0] != 0x7f || ehdr->e_ident[1] != 'E' || ehdr->e_ident[2] != 'L' || ehdr->e_ident[3] != 'F') {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_machine != 62 || ehdr->e_phentsize != sizeof(Elf64_Phdr) || ehdr->e_phnum == 0) {
        return EFI_LOAD_ERROR;
    }

    if (ehdr->e_phoff + (UINT64)ehdr->e_phentsize * (UINT64)ehdr->e_phnum > kernel_file_size) {
        return EFI_LOAD_ERROR;
    }

    status = find_bootmeta(kernel_file, kernel_file_size, entry64);
    if (EFI_ERROR(status)) {
        return status;
    }

    program_headers = (const Elf64_Phdr *)(file_bytes + ehdr->e_phoff);
    image_base = ~0ULL;
    image_end = 0;

    for (i = 0; i < ehdr->e_phnum; ++i) {
        const Elf64_Phdr *phdr;
        UINT64 segment_addr;

        phdr = &program_headers[i];
        if (phdr->p_type != PT_LOAD || phdr->p_memsz == 0) {
            continue;
        }

        if (phdr->p_offset + phdr->p_filesz > kernel_file_size) {
            return EFI_LOAD_ERROR;
        }

        segment_addr = phdr->p_paddr != 0 ? phdr->p_paddr : phdr->p_vaddr;
        if (align_down(segment_addr, 4096) < image_base) {
            image_base = align_down(segment_addr, 4096);
        }
        if (align_up(segment_addr + phdr->p_memsz, 4096) > image_end) {
            image_end = align_up(segment_addr + phdr->p_memsz, 4096);
        }
    }

    if (image_base == ~0ULL || image_end <= image_base) {
        return EFI_LOAD_ERROR;
    }

    image_addr = image_base;
    status = system_table->BootServices->AllocatePages(AllocateAddress,
                                                       EfiLoaderData,
                                                       (UINTN)((image_end - image_base) / 4096),
                                                       &image_addr);
    if (EFI_ERROR(status)) {
        return status;
    }

    mem_set((VOID *)(UINTN)image_base, 0, (UINTN)(image_end - image_base));

    for (i = 0; i < ehdr->e_phnum; ++i) {
        const Elf64_Phdr *phdr;
        UINT64 segment_addr;

        phdr = &program_headers[i];
        if (phdr->p_type != PT_LOAD || phdr->p_memsz == 0) {
            continue;
        }

        segment_addr = phdr->p_paddr != 0 ? phdr->p_paddr : phdr->p_vaddr;
        mem_copy((VOID *)(UINTN)segment_addr, file_bytes + phdr->p_offset, (UINTN)phdr->p_filesz);
    }

    *kernel_phys_base = image_base;
    *kernel_phys_end = image_end;
    return EFI_SUCCESS;
}

static VOID fill_boot_info(BOOT_INFO_BLOCK *boot_info,
                           MEMORY_REGION *regions,
                           UINT64 region_count,
                           UINT64 kernel_phys_base,
                           UINT64 kernel_phys_end) {
    UINTN i;

    for (i = 0; i < 21; ++i) {
        boot_info->Signature[i] = 0;
    }

    boot_info->Signature[0] = BOOT_INFO_MAGIC;
    boot_info->Signature[1] = 1;
    boot_info->Signature[2] = 2;
    boot_info->Signature[3] = (UINT64)(UINTN)regions;
    boot_info->Signature[4] = region_count;
    boot_info->Signature[5] = 0;
    boot_info->Signature[6] = 0;
    boot_info->Signature[7] = 0;
    boot_info->Signature[8] = 0;
    boot_info->Signature[9] = 0;
    boot_info->Signature[10] = 0;
    boot_info->Signature[11] = 0;
    boot_info->Signature[12] = 0;
    boot_info->Signature[13] = kernel_phys_base;
    boot_info->Signature[14] = kernel_phys_end;
    boot_info->Signature[15] = kernel_phys_base;
    boot_info->Signature[16] = kernel_phys_end;
    boot_info->Signature[17] = current_apic_id();
    boot_info->Signature[18] = 1;
    boot_info->Signature[19] = 0;
    boot_info->Signature[20] = 0;
}

typedef void (*KERNEL_ENTRY64)(UINT64);

EFI_STATUS efi_main_body(EFI_HANDLE image_handle, EFI_SYSTEM_TABLE *system_table) {
    EFI_STATUS status;
    EFI_FILE_PROTOCOL *root;
    VOID *kernel_file;
    UINTN kernel_file_size;
    UINT64 entry64;
    UINT64 kernel_phys_base;
    UINT64 kernel_phys_end;
    EFI_MEMORY_DESCRIPTOR *memory_map;
    UINTN memory_map_size;
    UINTN map_key;
    UINTN descriptor_size;
    UINT32 descriptor_version;
    EFI_PHYSICAL_ADDRESS boot_info_addr;
    EFI_PHYSICAL_ADDRESS region_addr;
    BOOT_INFO_BLOCK *boot_info;
    MEMORY_REGION *regions;
    UINT64 region_capacity;
    UINT64 region_count;

    root = NULL;
    kernel_file = NULL;
    kernel_file_size = 0;
    entry64 = 0;
    kernel_phys_base = 0;
    kernel_phys_end = 0;
    memory_map = NULL;
    memory_map_size = 0;
    map_key = 0;
    descriptor_size = 0;
    descriptor_version = 0;
    boot_info_addr = 0;
    region_addr = 0;

    efi_puts(system_table, L"PCO/OS UEFI loader\r\n");

    status = open_root(image_handle, system_table, &root);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"open root failed\r\n");
        return status;
    }

    status = read_entire_file(system_table, root, L"\\KERNEL.ELF", &kernel_file, &kernel_file_size);
    root->Close(root);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"read kernel failed\r\n");
        return status;
    }

    status = load_kernel_image(system_table, kernel_file, kernel_file_size, &entry64, &kernel_phys_base, &kernel_phys_end);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"load kernel failed\r\n");
        return status;
    }

    status = system_table->BootServices->GetMemoryMap(&memory_map_size, NULL, &map_key, &descriptor_size, &descriptor_version);
    if (status != EFI_BUFFER_TOO_SMALL || descriptor_size == 0) {
        efi_puts(system_table, L"memory map probe failed\r\n");
        return EFI_LOAD_ERROR;
    }

    memory_map_size += descriptor_size * 32;
    status = system_table->BootServices->AllocatePool(EfiLoaderData, memory_map_size, (VOID **)&memory_map);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"memory map alloc failed\r\n");
        return status;
    }

    region_capacity = (UINT64)(memory_map_size / descriptor_size) + 32;
    region_addr = 0;
    status = system_table->BootServices->AllocatePages(AllocateAnyPages,
                                                       EfiLoaderData,
                                                       (UINTN)align_up(region_capacity * sizeof(MEMORY_REGION), 4096) / 4096,
                                                       &region_addr);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"region alloc failed\r\n");
        return status;
    }

    boot_info_addr = 0;
    status = system_table->BootServices->AllocatePages(AllocateAnyPages, EfiLoaderData, 1, &boot_info_addr);
    if (EFI_ERROR(status)) {
        efi_puts(system_table, L"boot info alloc failed\r\n");
        return status;
    }

    for (;;) {
        UINTN current_map_size;
        UINT8 *descriptor_ptr;
        UINT64 index;

        current_map_size = memory_map_size;
        status = system_table->BootServices->GetMemoryMap(&current_map_size, memory_map, &map_key, &descriptor_size, &descriptor_version);
        if (EFI_ERROR(status)) {
            efi_puts(system_table, L"get memory map failed\r\n");
            return status;
        }

        regions = (MEMORY_REGION *)(UINTN)region_addr;
        region_count = (UINT64)(current_map_size / descriptor_size);
        descriptor_ptr = (UINT8 *)memory_map;
        for (index = 0; index < region_count; ++index) {
            EFI_MEMORY_DESCRIPTOR *desc;

            desc = (EFI_MEMORY_DESCRIPTOR *)(descriptor_ptr + index * descriptor_size);
            regions[index].Base = desc->PhysicalStart;
            regions[index].Length = desc->NumberOfPages << 12;
            regions[index].Type = desc->Type;
            regions[index].Attrs = desc->Attribute;
        }

        boot_info = (BOOT_INFO_BLOCK *)(UINTN)boot_info_addr;
        fill_boot_info(boot_info, regions, region_count, kernel_phys_base, kernel_phys_end);

        status = system_table->BootServices->ExitBootServices(image_handle, map_key);
        if (status == EFI_INVALID_PARAMETER) {
            continue;
        }
        if (EFI_ERROR(status)) {
            return status;
        }
        break;
    }

    ((KERNEL_ENTRY64)(UINTN)entry64)((UINT64)(UINTN)boot_info_addr);
    for (;;) {
    }
}

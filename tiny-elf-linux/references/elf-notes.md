# ELF Notes

## ELF64 Conservative Shape

- 64-byte ELF header.
- One 56-byte `PT_LOAD` program header.
- Code starts after headers.
- No section header table is needed for execution.

## ELF32 Conservative Shape

- 52-byte ELF header.
- One 32-byte `PT_LOAD` program header.
- Code starts after headers.
- Use `EM_386` and `ET_EXEC` for i386.

## Aggressive Overlap

ELF loaders need the ELF header and program headers, not section headers. This creates room to overlap unused section-header fields and sometimes unused program-header fields with meaningful bytes. Keep `e_phentsize`, `e_phnum`, `PT_LOAD`, `p_offset`, `p_vaddr`, `p_filesz`, `p_memsz`, and executable flags coherent.

## Common Minimal Fields

| Field | Why it matters |
| --- | --- |
| `e_ident` | Loader recognizes ELF class and endianness |
| `e_machine` | Must match CPU |
| `e_entry` | First instruction address |
| `e_phoff`/`e_phnum` | Loader finds loadable segments |
| `PT_LOAD` | Maps file bytes into memory |
| `p_flags` | Must allow execution for code |

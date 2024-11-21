import copy
import os
import re
import subprocess
import sys
import tempfile

from pathlib import Path
from typing import List, Optional, Tuple

from .elf import Elf, TextSection, Relocation


INCLUDE_ASM = "INCLUDE_ASM"
INCLUDE_ASM_REGEX = r'INCLUDE_ASM\("(.*)", (.*)\)'

INCLUDE_RODATA = "INCLUDE_RODATA"
INCLUDE_RODATA_REGEX = r'INCLUDE_RODATA\("(.*)", (.*)\)'

FUNCTION_PREFIX = "mwccgap_"


def assemble_file(
    asm_filepath: Path,
    as_path="mipsel-linux-gnu-as",
    as_march="allegrex",
    as_mabi="32",
    as_flags: Optional[List[str]] = None,
    macro_inc_path: Optional[Path] = None,
) -> bytes:
    if as_flags is None:
        as_flags = []

    with tempfile.NamedTemporaryFile(suffix=".o") as temp_file:
        cmd = [
            as_path,
            "-EL",
            f"-march={as_march}",
            f"-mabi={as_mabi}",
            "-Iinclude",
            "-o",
            temp_file.name,
            *as_flags,
        ]
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
            in_bytes = asm_filepath.read_bytes()
            if macro_inc_path and macro_inc_path.is_file():
                in_bytes = macro_inc_path.read_bytes() + in_bytes

            stdout, stderr = process.communicate(input=in_bytes)

        if len(stdout) > 0:
            sys.stderr.write(stdout.decode("utf"))
        if len(stderr) > 0:
            sys.stderr.write(stderr.decode("utf"))

        obj_bytes = temp_file.read()
        if len(obj_bytes) == 0:
            raise Exception(f"Failed to assemble {asm_filepath} (object is empty)")

    return obj_bytes


def preprocess_c_file(
    c_file, asm_dir_prefix=None
) -> Tuple[List[str], List[Tuple[Path, int]]]:
    with open(c_file, "r") as f:
        lines = f.readlines()

    out_lines: List[str] = []
    asm_files: List[Tuple[Path, int]] = []
    for i, line in enumerate(lines):
        line = line.rstrip()

        if line.startswith(INCLUDE_ASM) or line.startswith(INCLUDE_RODATA):

            if line.startswith(INCLUDE_ASM):
                macro = INCLUDE_ASM
                regex = INCLUDE_ASM_REGEX
            else:

                macro = INCLUDE_RODATA
                regex = INCLUDE_RODATA_REGEX

            if not (match := re.match(regex, line)):
                raise Exception(
                    f"{c_file} contains invalid {macro} macro on line {i}: {line}"
                )
            try:
                asm_dir = Path(match.group(1))
                asm_function = match.group(2)
            except Exception as e:
                raise Exception(
                    f"{c_file} contains invalid {macro} macro on line {i}: {line}"
                ) from e

            asm_file = asm_dir / f"{asm_function}.s"
            if asm_dir_prefix is not None:
                asm_file = asm_dir_prefix / asm_file

            if not asm_file.is_file():
                raise Exception(
                    f"{c_file} includes asm {asm_file} that does not exist on line {i}: {line}"
                )

            in_rodata = False
            rodata_entries = {}
            nops_needed = 0

            for asm_line in asm_file.read_text().split("\n"):
                asm_line = asm_line.strip()
                if not asm_line:
                    # skip empty lines
                    continue

                if asm_line.startswith(".section"):
                    if asm_line.endswith(".text"):
                        in_rodata = False
                        continue
                    elif asm_line.endswith(".rodata") or asm_line.endswith(
                        ".late_rodata"
                    ):
                        in_rodata = True
                        continue

                    raise Exception(f"Unsupported .section: {asm_line}")

                if in_rodata:
                    if asm_line.startswith(".align"):
                        continue
                    if asm_line.startswith(".size"):
                        continue
                    if asm_line.startswith("glabel") or asm_line.startswith("dlabel"):
                        _, rodata_symbol = asm_line.split(" ")
                        rodata_entries[rodata_symbol] = 0
                        continue
                    if asm_line.find(" .byte ") > -1:
                        rodata_entries[rodata_symbol] += 1
                        continue
                    if asm_line.find(" .short ") > -1:
                        rodata_entries[rodata_symbol] += 2
                        continue
                    if asm_line.find(" .word ") > -1:
                        rodata_entries[rodata_symbol] += 4
                        continue

                    raise Exception(f"Unexpected entry in .rodata: {asm_line}")

                if asm_line.startswith(".set"):
                    # ignore set
                    continue
                if asm_line.startswith(".include"):
                    # ignore include
                    continue
                if asm_line.startswith(".size"):
                    # ignore size
                    continue
                if asm_line.startswith(".align") or asm_line.startswith(".balign"):
                    # ignore alignment
                    continue
                if asm_line.startswith("glabel") or asm_line.startswith("jlabel"):
                    # ignore function / jumptable labels
                    continue
                if asm_line.startswith(".L") and asm_line.endswith(":"):
                    # ignore labels
                    continue
                if asm_line.startswith("/* Generated by spimdisasm"):
                    # ignore spim
                    continue
                if asm_line.startswith("/* Handwritten function"):
                    # ignore handwritten comment
                    continue

                nops_needed += 1

            if nops_needed > 0:
                nops = nops_needed * ["nop"]
                out_lines.extend(
                    [f"asm void {FUNCTION_PREFIX}{asm_function}() {'{'}", *nops, "}"]
                )

            for symbol, size in rodata_entries.items():
                out_lines.append(
                    f"const unsigned char {symbol}[{size}] = {'{'}"
                    + size * "0, "
                    + "};",
                )

            asm_files.append((asm_file, len(rodata_entries)))

        else:
            out_lines.append(line)

    return (out_lines, asm_files)


def compile_file_helper(
    c_file: Path,
    o_file: Path,
    c_flags: Optional[List[str]],
    mwcc_path: Path,
    use_wibo: bool,
    wibo_path: Path,
):
    o_file.parent.mkdir(exist_ok=True, parents=True)
    o_file.unlink(missing_ok=True)

    cmd = [
        str(mwcc_path),
        "-c",
        *(c_flags if c_flags else []),
        "-o",
        str(o_file),
        str(c_file),
    ]
    if use_wibo:
        cmd.insert(0, str(wibo_path))

    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(os.environ, MWCIncludes="."),
    ) as proc:
        return proc.communicate()


def compile_file(
    c_file: Path,
    c_flags: Optional[List[str]],
    mwcc_path: Path,
    use_wibo: bool,
    wibo_path: Path,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        o_file = Path(temp_dir) / "result.o"
        stdout, stderr = compile_file_helper(
            c_file,
            o_file,
            c_flags,
            mwcc_path,
            use_wibo,
            wibo_path,
        )

        if len(stdout) > 0:
            sys.stderr.write(stdout.decode("utf"))
        if len(stderr) > 0:
            sys.stderr.write(stderr.decode("utf"))

        if not o_file.is_file():
            raise Exception(f"Error compiling {c_file}")

        obj_bytes = o_file.read_bytes()
        if len(obj_bytes) == 0:
            raise Exception(f"Error compiling {c_file}, object is empty")

    return obj_bytes


def process_c_file(
    c_file: Path,
    o_file: Path,
    c_flags=None,
    mwcc_path="mwccpsp.exe",
    as_path="mipsel-linux-gnu-as",
    as_flags=None,
    as_march="allegrex",
    as_mabi="32",
    use_wibo=False,
    wibo_path="wibo",
    asm_dir_prefix=None,
    macro_inc_path: Optional[Path] = None,
):
    # 1. compile file as-is, any INCLUDE_ASM'd functions will be missing from the object
    obj_bytes = compile_file(c_file, c_flags, mwcc_path, use_wibo, wibo_path)
    precompiled_elf = Elf(obj_bytes)

    # 2. identify all INCLUDE_ASM statements and replace with asm statements full of nops
    out_lines, asm_files = preprocess_c_file(c_file, asm_dir_prefix=asm_dir_prefix)

    # for now we only care about the names of the functions that exist
    c_functions = [f.function_name for f in precompiled_elf.get_functions()]

    # filter out functions that can be found in the compiled c object
    asm_files = [(x, y) for (x, y) in asm_files if x.stem not in c_functions]

    # if there's nothing to do, write out the bytes from the precompiled object
    if len(asm_files) == 0:
        o_file.parent.mkdir(exist_ok=True, parents=True)
        with o_file.open("wb") as f:
            f.write(obj_bytes)
        return

    # 3. compile the modified .c file for real
    with tempfile.NamedTemporaryFile(suffix=".c", dir=c_file.parent) as temp_c_file:
        temp_c_file.write("\n".join(out_lines).encode("utf"))
        temp_c_file.flush()

        obj_bytes = compile_file(
            Path(temp_c_file.name), c_flags, mwcc_path, use_wibo, wibo_path
        )

    compiled_elf = Elf(obj_bytes)

    rel_text_sh_name = compiled_elf.add_sh_symbol(".rel.text")

    for symbol in compiled_elf.symtab.symbols:
        if symbol.name.startswith(FUNCTION_PREFIX):
            symbol.name = symbol.name[len(FUNCTION_PREFIX) :]
            symbol.st_name += len(FUNCTION_PREFIX)

    symbol_to_rodata_idx = {}
    for i, section in enumerate(compiled_elf.sections):
        if section.name == ".rodata":
            for symbol in compiled_elf.symtab.symbols:
                if symbol.st_shndx == i:
                    symbol_to_rodata_idx[symbol.name] = i

    for asm_file, num_rodata_symbols in asm_files:
        function = asm_file.stem

        asm_bytes = assemble_file(
            asm_file,
            as_path=as_path,
            as_flags=as_flags,
            as_march=as_march,
            as_mabi=as_mabi,
            macro_inc_path=macro_inc_path,
        )
        assembled_elf = Elf(asm_bytes)

        asm_functions = assembled_elf.get_functions()
        assert (
            len(asm_functions) == 1
        ), f"Maximum of 1 function per asm file (found {len(asm_functions)})"

        asm_text = asm_functions[0].data
        has_text = len(asm_text) > 0

        if has_text:
            # identify the .text section for this function
            for text_section_index, text_section in enumerate(compiled_elf.sections):
                if (
                    isinstance(text_section, TextSection)
                    and text_section.function_name == f"{FUNCTION_PREFIX}{function}"
                ):
                    break
            else:
                raise Exception(f"{function} not found in {c_file}")

            # assumption is that .rodata will immediately follow the .text section
            rodata_section_indices = []
            if num_rodata_symbols > 0:
                for i, section in enumerate(
                    compiled_elf.sections[text_section_index + 1 :]
                ):
                    if section.name == ".rodata":
                        # found some .rodata before another .text section
                        rodata_section_indices.append(text_section_index + 1 + i)
                        if len(rodata_section_indices) == num_rodata_symbols:
                            # reached end of rodata sections for this text section
                            break

            assert num_rodata_symbols == len(
                rodata_section_indices
            ), ".rodata section count mismatch"
        else:
            assert (
                num_rodata_symbols == 1
            ), f"Maximum of 1 symbol per rodata asm file (found {num_rodata_symbols})"
            idx = symbol_to_rodata_idx.get(function)
            assert (
                idx is not None
            ), f"Could not find .rodata section for symbol '{function}'"
            rodata_section_indices = [idx]

        if has_text:
            # transplant .text section data from assembled object
            compiled_function_length = len(text_section.data)

            assert (
                len(asm_text) >= compiled_function_length
            ), f"Not enough assembly to fill {function} in {c_file}"

            text_section.data = asm_text[:compiled_function_length]

        if num_rodata_symbols > 0:
            assert (
                len(assembled_elf.rodata_sections) == 1
            ), f"Expected ASM to contain 1 .rodata section, found {len(assembled_elf.rodata_sections)}"
            asm_rodata = assembled_elf.rodata_sections[0]

            offset = 0
            rodata_section_offsets = []
            for idx in rodata_section_indices:
                # copy slices of rodata from ASM object into each .rodata section
                data_len = len(compiled_elf.sections[idx].data)
                compiled_elf.sections[idx].data = asm_rodata.data[
                    offset : offset + data_len
                ]
                offset += data_len
                rodata_section_offsets.append(offset)

                # force 4-byte alignment for .rodata sections (defaults to 16-byte)
                compiled_elf.sections[idx].sh_addralign = 4

            rel_rodata_sh_name = compiled_elf.add_sh_symbol(".rel.rodata")

        relocation_records = assembled_elf.get_relocations()
        assert (
            len(relocation_records) < 3
        ), f"{asm_file} has too many relocation records!"

        reloc_symbols = set()

        initial_sh_info_value = compiled_elf.symtab.sh_info
        local_syms_inserted = 0

        # assumes .text relocations precede .rodata relocations
        for i, relocation_record in enumerate(relocation_records):
            relocation_record.sh_link = compiled_elf.symtab_index
            if has_text and i == 0:
                relocation_record.sh_name = rel_text_sh_name
                relocation_record.sh_info = text_section_index
            else:
                relocation_record.sh_name = rel_rodata_sh_name
                relocation_record.sh_info = rodata_section_indices[0]

            for relocation in relocation_record.relocations:
                symbol = assembled_elf.symtab.symbols[relocation.symbol_index]

                if symbol.bind == 0:
                    local_syms_inserted += 1

                if has_text and i == 0:
                    force = False
                else:
                    force = True

                relocation.symbol_index = compiled_elf.add_symbol(symbol, force=force)
                reloc_symbols.add(symbol.name)

                if has_text and i == 1:
                    # repoint .rodata reloc to .text section
                    symbol.st_shndx = text_section_index

            compiled_elf.add_section(relocation_record)

        new_rodata_relocs = []
        if local_syms_inserted > 0:
            # update relocations
            for relocation_record in compiled_elf.get_relocations():
                if relocation_record.sh_info == rodata_section_indices[0]:
                    if num_rodata_symbols == 1:
                        # nothing to do when only a single .rodata section
                        continue

                    # otherwise we need to split the rodata relocations across each .rodata section
                    new_relocations: List[List[Relocation]] = [
                        [] for _ in rodata_section_indices
                    ]
                    for relocation in relocation_record.relocations:
                        for i in range(len(rodata_section_offsets)):
                            if relocation.r_offset < rodata_section_offsets[i]:
                                if i > 0:
                                    relocation.r_offset -= rodata_section_offsets[i - 1]
                                new_relocations[i].append(relocation)
                                break

                    for i, relocations in enumerate(new_relocations):
                        if i == 0:
                            # amend original in place
                            new_rodata_reloc = relocation_record
                        else:
                            # take a copy of the original
                            new_rodata_reloc = copy.copy(relocation_record)

                        new_rodata_reloc.relocations = relocations
                        new_rodata_reloc.sh_info = rodata_section_indices[i]
                        new_rodata_relocs.append(new_rodata_reloc)

                    continue

                for relocation in relocation_record.relocations:
                    if relocation.symbol_index >= initial_sh_info_value:
                        relocation.symbol_index += local_syms_inserted

            for new_rodata_reloc in new_rodata_relocs[1:]:
                compiled_elf.add_section(new_rodata_reloc)

        for symbol in assembled_elf.symtab.symbols:
            if symbol.st_name == 0:
                continue

            if symbol.bind == 0:
                # ignore local symbols
                continue

            if has_text and symbol.name not in reloc_symbols:
                symbol.st_shndx = text_section_index
                compiled_elf.add_symbol(symbol)

    o_file.parent.mkdir(exist_ok=True, parents=True)
    with o_file.open("wb") as f:
        f.write(compiled_elf.pack())

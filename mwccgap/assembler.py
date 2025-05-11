import subprocess
import sys
import tempfile

from pathlib import Path
from typing import Optional

from .exceptions import AssemblerException


class Assembler:
    def __init__(
        self,
        as_path="mipsel-linux-gnu-as",
        as_march="allegrex",
        as_mabi="32",
        as_flags: Optional[list[str]] = None,
        macro_inc_path: Optional[Path] = None,
    ):
        if as_flags is None:
            as_flags = []

        self.as_path = as_path
        self.as_march = as_march
        self.as_mabi = as_mabi
        self.as_flags = as_flags
        self.macro_inc_path = macro_inc_path

    def assemble_file(
        self,
        asm_filepath: Path,
    ) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".o") as temp_file:
            cmd = [
                self.as_path,
                "-EL",
                f"-march={self.as_march}",
                f"-mabi={self.as_mabi}",
                "-o",
                temp_file.name,
                *self.as_flags,
            ]

            if self.macro_inc_path:
                cmd.insert(4, f"-I{str(self.macro_inc_path.resolve().parent)}")

            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as process:
                in_bytes = asm_filepath.read_bytes()
                if self.macro_inc_path and self.macro_inc_path.is_file():
                    in_bytes = self.macro_inc_path.read_bytes() + in_bytes

                stdout, stderr = process.communicate(input=in_bytes)

            if stdout:
                sys.stderr.write(stdout.decode("utf-8"))
            if stderr:
                sys.stderr.write(stderr.decode("utf-8"))

            if process.returncode != 0:
                raise AssemblerException(
                    f"Failed to assemble {asm_filepath} (assembler returned {process.returncode})"
                )

            obj_bytes = temp_file.read()

        if len(obj_bytes) == 0:
            raise AssemblerException(
                f"Failed to assemble {asm_filepath} (object is empty)"
            )

        return obj_bytes

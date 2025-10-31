import os
import re
import subprocess
import sys
import tempfile

from pathlib import Path
from typing import List, Optional
from .makerule import MakeRule


class Compiler:
    obj_bytes: bytes | None
    make_rule: MakeRule | None

    def __init__(
        self,
        c_flags: Optional[List[str]],
        mwcc_path: Path,
        use_wibo: bool,
        wibo_path: Path,
    ):
        if c_flags is None:
            c_flags = []

        self.c_flags = c_flags
        self.mwcc_path = mwcc_path
        self.use_wibo = use_wibo
        self.wibo_path = wibo_path
        self.obj_bytes = None
        self.make_rule = None

        # gcc compatibility may be enabled and then
        # disabled by a later flag
        self.gcc_deps = False
        for flag in self.c_flags:
            if flag in ["-gccdep", "-gccdepends"]:
                self.gcc_deps = True
            if flag in ["-nogccdep", "-nogccdepends"]:
                self.gcc_deps = False

    def _compile_file(
        self,
        c_file: Path,
        o_file: Path,
    ) -> tuple[bytes, bytes]:
        o_file.parent.mkdir(exist_ok=True, parents=True)
        o_file.unlink(missing_ok=True)

        cmd = [
            str(self.mwcc_path),
            "-c",
            *self.c_flags,
            "-o",
            str(o_file),
            str(c_file),
        ]
        if self.use_wibo:
            cmd.insert(0, str(self.wibo_path))

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(os.environ, MWCIncludes="."),  # TODO: remove this?
        ) as proc:
            return proc.communicate()

    def compile_file(
        self,
        c_file: Path,
    ) -> bytes:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            o_file = temp_path / "result.o"
            stdout, stderr = self._compile_file(
                c_file,
                o_file,
            )

            if stdout:
                sys.stderr.write(stdout.decode("utf-8"))
            if stderr:
                sys.stderr.write(stderr.decode("utf-8"))

            if not o_file.is_file():
                raise Exception(f"Error compiling {c_file}")

            self.obj_bytes = o_file.read_bytes()
            if len(self.obj_bytes) == 0:
                raise Exception(f"Error compiling {c_file}, object is empty")

            self._handle_dependency_file(c_file, temp_path)

        return self.obj_bytes

    # the compiler may emit a dependency file in addition to the object
    # file. if so, we want to make those bytes available to the caller
    def _handle_dependency_file(self, c_file: Path, temp_dir: Path):
        self.make_rule = None

        if self.gcc_deps:
            d_file = Path(temp_dir) / "result.d"
            if d_file.is_file():
                dep_bytes = d_file.read_bytes()
                self.make_rule = MakeRule(dep_bytes, self.use_wibo)
        elif "-MD" in self.c_flags or "-MMD" in self.c_flags:
            # in MetroWerks mode, the dependency file will be put in cwd
            # with the same name as the source file but with a .d extension
            d_file = Path(re.sub("\\.c$", ".d", c_file.name))
            if d_file.is_file():
                dep_bytes = d_file.read_bytes()
                d_file.unlink()
                self.make_rule = MakeRule(dep_bytes, self.use_wibo)

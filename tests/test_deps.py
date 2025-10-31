import tempfile
import unittest
import os
import re
import shutil

from pathlib import Path
from mwccgap.compiler import Compiler
from mwccgap.makerule import MakeRule

mwcc = os.getenv("MWCC")
if mwcc is None:
    mwcc = "mwccpsp.exe"


def has_wibo_and_mwcc():
    wibo = shutil.which("wibo")
    mwcc_exe = shutil.which(mwcc)
    return wibo is not None and mwcc_exe is not None


class TestDependencies(unittest.TestCase):
    def __init__(self, x):
        super().__init__(x)
        self.wibo = shutil.which("wibo")
        self.mwcc = shutil.which(mwcc)

    def has_dependencies(self):
        return self.wibo is not None and self.mwcc is not None

    def _compile(self, c_flags: list[str], program: str):
        compiler = Compiler(c_flags, self.mwcc, True, self.wibo)

        test_path = os.path.abspath(__file__)
        test_dir = os.path.dirname(test_path)
        with tempfile.NamedTemporaryFile(suffix=".c", dir=test_dir) as c_file:
            c_file.write(program.encode("utf-8"))
            c_file.flush()
            compiler.compile_file(Path(c_file.name))

        return compiler

    @unittest.skipUnless(has_wibo_and_mwcc(), "requires wibo and mwcc")
    def test_dependencies_gcc_behavior(self):
        compiler = self._compile(
            ["-MD", "-gccdep"],
            """
int add(int a, int b) {
    return a + b;
}
""",
        )

        rule = compiler.make_rule

        self.assertTrue(
            str(rule.target).startswith("/tmp"),
            f"target: {rule.target} should start with /tmp",
        )
        self.assertTrue(
            str(rule.target).endswith("result.o"),
            f"target: {rule.target} should end with result.o",
        )
        self.assertTrue(str(rule.source).endswith(".c"))
        self.assertEqual(0, len(rule.includes))

    @unittest.skipUnless(has_wibo_and_mwcc(), "requires wibo and mwcc")
    def test_no_dependencies_mw_behavior(self):
        compiler = self._compile(
            ["-MD"],
            """int add(int a, int b) {
    return a + b;
}
""",
        )

        rule = compiler.make_rule

        self.assertTrue(
            str(rule.target).startswith("/tmp"),
            f"target: {rule.target} should start with /tmp",
        )
        self.assertTrue(
            str(rule.target).endswith("result.o"),
            f"target: {rule.target} should end with result.o",
        )
        self.assertTrue(str(rule.source).endswith(".c"))
        self.assertEqual(0, len(rule.includes))

    @unittest.skipUnless(has_wibo_and_mwcc(), "requires wibo and mwcc")
    def test_no_depencies(self):
        compiler = self._compile(
            [],
            """int add(int a, int b) {
    return a + b;
}
""",
        )

        rule = compiler.make_rule

        self.assertIsNone(rule)

    def test_make_rule_simple(self):
        wibo_make_rule = "Z:\\tmp\\tmpfmuzt8mz\\result.o: test.c \r\n".encode("ascii")

        rule = MakeRule(wibo_make_rule, True)

        self.assertEqual(Path("/tmp/tmpfmuzt8mz/result.o"), rule.target)
        self.assertEqual(Path("test.c"), rule.source)
        self.assertEqual([], rule.includes)
        self.assertEqual("/tmp/tmpfmuzt8mz/result.o: test.c \n", rule.as_str())

    def test_make_rule_with_includes(self):
        wibo_make_rule = (
            "Z:\\tmp\\tmpfkcxmvnu\\result.o: test2.c \\\r\n"
            "\tZ:\\home\\user\\Projects\\mwccgap\\decl.h \\\r\n"
            "\t\\\\?\\Z:\\home\\user\\Projects\\mwccgap\\lib.h \r\n"
        ).encode("ascii")

        rule = MakeRule(wibo_make_rule, True)

        expected_rule = (
            "/tmp/tmpfkcxmvnu/result.o: test2.c \\\n"
            "\t/home/user/Projects/mwccgap/decl.h \\\n"
            "\t/home/user/Projects/mwccgap/lib.h \n"
        )
        self.assertEqual(expected_rule, rule.as_str())

    def test_unix_deps(self):
        make_rule = (
            "/tmp/tmpfkcxmvnu/result.o: test.c \\\n" "\tdecl.h \\\n" "\tlib.h \n"
        ).encode("utf-8")

        rule = MakeRule(make_rule, False)

        self.assertEqual("/tmp/tmpfkcxmvnu/result.o", rule.target)
        self.assertEqual("test.c", rule.source)
        self.assertEqual(["decl.h", "lib.h"], rule.includes)
        self.assertEqual(make_rule.decode("utf-8"), rule.as_str())

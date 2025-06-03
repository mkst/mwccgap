import unittest


from mwccgap.preprocessor import Preprocessor


class TestPreprocessSFile(unittest.TestCase):
    def test_empty(self):
        c_lines, rodata_entries = Preprocessor().preprocess_s_file("empty.s", [])
        self.assertEqual(0, len(c_lines))
        self.assertEqual(0, len(rodata_entries))

    def test_empty_function(self):
        asm_contents = """
.section .text
glabel empty_func
""".strip()

        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "text_only.s", asm_contents.splitlines()
        )
        self.assertEqual(0, len(c_lines))
        self.assertEqual(0, len(rodata_entries))

    def test_simple(self):
        asm_contents = """
.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */
glabel Bg_Disp_Switch
    /* 710B0 00171030 F0FFBD27 */  addiu      $sp, $sp, -0x10
    /* 710B4 00171034 0000A4A3 */  sb         $a0, 0x0($sp)
    /* 710B8 00171038 0000A393 */  lbu        $v1, 0x0($sp)
    /* 710BC 0017103C D0E683A3 */  sb         $v1, %gp_rel(bg_disp_off)($gp)
    /* 710C0 00171040 1000BD27 */  addiu      $sp, $sp, 0x10
    /* 710C4 00171044 0800E003 */  jr         $ra
    /* 710C8 00171048 00000000 */   nop
.size Bg_Disp_Switch, . - Bg_Disp_Switch
    /* 710CC 0017104C 00000000 */  nop
""".strip()
        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "simple.s", asm_contents.splitlines()
        )

        expected_nops = 8
        self.assertEqual(expected_nops + 2, len(c_lines))
        self.assertEqual(0, len(rodata_entries))

    def test_rodata_words(self):
        asm_contents = """
.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */
.section .rodata
.align 3
dlabel literal_515_00552620
    /* 4526A0 00552620 086B3900 */ .word 0x00396B08
    /* 4526A4 00552624 086B3900 */ .word 0x00396B08
    /* 4526A8 00552628 D06A3900 */ .word 0x00396AD0
    /* 4526AC 0055262C 086B3900 */ .word 0x00396B08
    /* 4526B0 00552630 D06A3900 */ .word 0x00396AD0
    /* 4526B4 00552634 306A3900 */ .word 0x00396A30
    /* 4526B8 00552638 E86A3900 */ .word 0x00396AE8
    /* 4526BC 0055263C 586A3900 */ .word 0x00396A58
    /* 4526C0 00552640 086B3900 */ .word 0x00396B08
    /* 4526C4 00552644 786A3900 */ .word 0x00396A78
    /* 4526C8 00552648 00000000 */ .word 0x00000000
    /* 4526CC 0055264C 00000000 */ .word 0x00000000
.size literal_515_00552620, . - literal_515_00552620
""".strip()
        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "rodata.s", asm_contents.splitlines()
        )

        self.assertEqual(1, len(c_lines))
        self.assertEqual(1, len(rodata_entries))
        self.assertIn("literal_515_00552620", rodata_entries)
        self.assertEqual(12 * 4, rodata_entries["literal_515_00552620"].size)

    def test_rodata_asciz(self):
        asm_contents = """
.section .rodata

.align 2
dlabel foobar
    /* 1DAB48 002DAAC8 */ .asciz "SHAUN PALMER"
.align 2
.size foobar, . - foobar
""".strip()

        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "asciz.s", asm_contents.splitlines()
        )

        self.assertEqual(1, len(c_lines))
        self.assertEqual(1, len(rodata_entries))
        self.assertIn("foobar", rodata_entries)
        self.assertEqual((len("SHAUN PALMER") + 1) * 1, rodata_entries["foobar"].size)

    def test_ascii_with_escaped_chars(self):
        asm_contents = """
.section .rodata
dlabel hello
    /* 1DAB48 002DAAC8 */ .ascii "Line1\\nLine2"
""".strip()

        _, rodata_entries = Preprocessor().preprocess_s_file(
            "ascii.s", asm_contents.splitlines()
        )
        self.assertEqual(len("Line1\nLine2"), rodata_entries["hello"].size)

    def test_rodata_float(self):
        asm_contents = """
.section .rodata

dlabel _1024sintable45
    /* 1E5000 002E4F80 00000000 */ .float 0
    /* 1E5004 002E4F84 F3043544 */ .float 724.0773315
    /* 1E5008 002E4F88 00008044 */ .float 1024
    /* 1E500C 002E4F8C F3043544 */ .float 724.0773315
    /* 1E5010 002E4F90 00000000 */ .float 0
    /* 1E5014 002E4F94 F30435C4 */ .float -724.0773315
    /* 1E5018 002E4F98 000080C4 */ .float -1024
    /* 1E501C 002E4F9C F30435C4 */ .float -724.0773315
    /* 1E5020 002E4FA0 00000000 */ .float 0
    /* 1E5024 002E4FA4 00000000 */ .float 0
    /* 1E5028 002E4FA8 00000000 */ .float 0
    /* 1E502C 002E4FAC 00000000 */ .float 0
.size _1024sintable45, . - _1024sintable45
""".strip()
        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "float.s", asm_contents.splitlines()
        )

        self.assertEqual(1, len(c_lines))
        self.assertEqual(1, len(rodata_entries))
        self.assertIn("_1024sintable45", rodata_entries)
        self.assertEqual(12 * 4, rodata_entries["_1024sintable45"].size)

    def test_local_symbol(self):
        asm_contents = """
.section .rodata

glabel D_psp_0914A7B8, local
    /* 6DE38 0914A7B8 */ .word 0x12345678
        """
        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "local.s", asm_contents.splitlines()
        )

        self.assertEqual(1, len(c_lines))
        self.assertEqual(1, len(rodata_entries))
        self.assertIn("D_psp_0914A7B8", rodata_entries)
        self.assertEqual(1 * 4, rodata_entries["D_psp_0914A7B8"].size)
        self.assertTrue(rodata_entries["D_psp_0914A7B8"].local)
        self.assertTrue(c_lines[0].startswith("static "))

    def test_dollar_symbol(self):
        asm_contents = """
.section .rodata

dlabel foo$bar$baz
    /* 1E5000 002E4F80 00000000 */ .word 0x1234
.size foo$bar$baz, . - foo$bar$baz
"""
        c_lines, rodata_entries = Preprocessor().preprocess_s_file(
            "dollar.s", asm_contents.splitlines()
        )
        expected_symbol_name = "foo$bar$baz"

        self.assertEqual(1, len(c_lines))
        self.assertEqual(1, len(rodata_entries))
        self.assertIn(expected_symbol_name, rodata_entries)
        self.assertEqual(1 * 4, rodata_entries[expected_symbol_name].size)
        self.assertTrue(rodata_entries[expected_symbol_name].local)
        self.assertTrue(c_lines[0].startswith("static "))


class TestPreprocessSFileExceptions(unittest.TestCase):
    def test_rodata_unknown_directive(self):
        asm_contents = """
.section .rodata
dlabel my_literal
    .weird 0x1234
""".strip()

        with self.assertRaises(ValueError) as e:
            Preprocessor().preprocess_s_file("unknown.s", asm_contents.splitlines())
        self.assertIn("Unexpected entry", str(e.exception))

    def test_malformed_label(self):
        asm_contents = """
.section .rodata
glabel
    .word 0x12345678
""".strip()

        with self.assertRaises(ValueError):
            Preprocessor().preprocess_s_file("bad_label.s", asm_contents.splitlines())

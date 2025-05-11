import unittest


from mwccgap.preprocessor import Preprocessor


class TestPreprocessSFile(unittest.TestCase):
    def test_empty(self):
        c_lines, rodata_entries = Preprocessor().preprocess_s_file("empty.s", [])
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
        self.assertTrue("literal_515_00552620" in rodata_entries)
        self.assertEqual(12 * 4, rodata_entries["literal_515_00552620"])

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
        self.assertTrue("foobar" in rodata_entries)
        self.assertEqual(13 * 1, rodata_entries["foobar"])

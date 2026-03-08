import unittest


from mwccgap.mwccgap import replace_sinit


class TestSinitSymbolNames(unittest.TestCase):
    def test_short_filename(self):
        c_file_name = "short.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f".p__sinit_{temp_f_name}"
        expect_name = f".p__sinit_{c_file_name}"

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

    def test_long_filename(self):
        c_file_name = "extra_long_name.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f"__sinit_{temp_f_name}"
        expect_name = f"__sinit_{c_file_name}"

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

    def test_short_filename_bugged_symbols(self):
        c_file_name = "short.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f".p__sinit_{temp_f_name.ljust(ord(temp_f_name[0]))}"
        expect_name = f".p__sinit_{c_file_name.ljust(ord(c_file_name[0]))}"

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

    def test_long_filename_bugged_symbols(self):
        c_file_name = "extra_long_name.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f"__sinit_{temp_f_name.ljust(ord(temp_f_name[0]))}"
        expect_name = f"__sinit_{c_file_name.ljust(ord(c_file_name[0]))}"

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

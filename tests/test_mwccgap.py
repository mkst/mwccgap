import unittest


from mwccgap.mwccgap import replace_sinit


class TestPreprocessSFile(unittest.TestCase):
    def test_unrelated(self):
        symbol_name = "some_function"
        result = replace_sinit(symbol_name, "tmp12234567.c", "test.cpp")
        self.assertEqual(symbol_name, result)

    def test_short_filename(self):
        c_file_name = "short.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f".p__sinit_{temp_f_name}".ljust(253)
        expect_name = f".p__sinit_{c_file_name}".ljust(253)

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

    def test_long_filename(self):
        c_file_name = "extra_long_name.cpp"
        temp_f_name = "tmp12456789.c"
        symbol_name = f"__sinit_{temp_f_name}".ljust(253)
        expect_name = f"__sinit_{c_file_name}".ljust(253)

        result = replace_sinit(symbol_name, temp_f_name, c_file_name)
        self.assertEqual(expect_name, result)

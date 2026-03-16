INCLUDE_ASM = "INCLUDE_ASM"
INCLUDE_ASM_REGEX = rf'{INCLUDE_ASM}\("(.*)", (.*)\)'

INCLUDE_RODATA = "INCLUDE_RODATA"
INCLUDE_RODATA_REGEX = rf'{INCLUDE_RODATA}\("(.*)", (.*)\)'

BLOCK_COMMENT_REGEX = r"/\*.*?\*/"

DOLLAR_SIGN = "$"

FUNCTION_PREFIX = "mwccgap_"
SYMBOL_AT = "__at__"
SYMBOL_DOLLAR = "__dollar__"
SYMBOL_SINIT = "__sinit_"

LOCAL_SUFFIX = ", local"

IGNORED_RELOCATIONS = (".rel.pdr",)

BEFORE_PREPROCESSED_LINES = """
#ifdef __cplusplus
extern "C" {
#endif
""".splitlines()

AFTER_PREPROCESSED_LINES = """
#ifdef __cplusplus
}
#endif
""".splitlines()

import argparse
import sys
import traceback

from pathlib import Path

from mwccgap.mwccgap import process_c_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("c_file", type=Path)
    parser.add_argument("o_file", type=Path)
    parser.add_argument("--mwcc-path", type=Path, default=Path("mwccpsp.exe"))
    parser.add_argument("--as-path", type=Path, default=Path("mipsel-linux-gnu-as"))
    parser.add_argument("--as-march", type=str, default="allegrex")
    parser.add_argument("--as-mabi", type=str, default="32")
    parser.add_argument("--use-wibo", action="store_true")
    parser.add_argument("--wibo-path", type=Path, default=Path("wibo"))
    parser.add_argument("--asm-dir-prefix", type=str)
    parser.add_argument("--macro-inc-path", type=Path)

    args, c_flags = parser.parse_known_args()

    as_flags = ["-G0"]  # TODO: base this on -sdatathreshold value from c_flags

    try:
        process_c_file(
            args.c_file,
            args.o_file,
            c_flags,
            mwcc_path=args.mwcc_path,
            as_path=args.as_path,
            as_march=args.as_march,
            as_mabi=args.as_mabi,
            use_wibo=args.use_wibo,
            wibo_path=args.wibo_path,
            as_flags=as_flags,
            asm_dir_prefix=args.asm_dir_prefix,
            macro_inc_path=args.macro_inc_path,
        )
    except Exception as e:
        sys.stderr.write(f"Exception processing {args.c_file}: {e}\n")
        sys.stderr.write(traceback.format_exc())
        sys.stderr.write("\n")
        # cleanup
        o_file.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

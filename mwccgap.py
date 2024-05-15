import argparse
import sys
import traceback

from pathlib import Path

from mwccgap.mwccgap import process_c_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("c_file", type=str)
    parser.add_argument("o_file", type=str)
    parser.add_argument("--mwcc-path", type=str, default="mwccpsp.exe")
    parser.add_argument("--as-path", type=str, default="mipsel-linux-gnu-as")
    parser.add_argument("--use-wibo", action="store_true")
    parser.add_argument("--wibo-path", type=str, default="wibo")

    args, c_flags = parser.parse_known_args()

    c_file = Path(args.c_file)
    o_file = Path(args.o_file)
    try:
        process_c_file(
            c_file,
            o_file,
            c_flags,
            mwcc_path=args.mwcc_path,
            as_path=args.as_path,
            use_wibo=args.use_wibo,
            wibo_path=args.wibo_path,
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

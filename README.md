# mwccgap AKA "MWCC Global Assembly Processor"

`mwccgap` is a tool that enables individual functions within a C file to be replaced with assembly code, drawing heavy inspiration from [asm-processor](https://github.com/simonlindholm/asm-processor).

While the MWCC compiler does support embedding raw assembly within a C file, it requires that all variables and functions be fully defined. This limitation makes the traditional [Ship of Theseus](https://en.wikipedia.org/wiki/Ship_of_Theseus) approach to matching decompiled code slow and cumbersome.

Unlike `asm-processor`, which uses a `GLOBAL_ASM` pragma, `mwccgap` adopts an `INCLUDE_ASM` macro to align with the needs of its first supported project, which uses GCC. Future updates may add support for both approaches.

When a function in a C file is marked defined using the `INCLUDE_ASM` macro, it is replaced with a series of `nop` instructions of the appropriate size during compilation. The C file is then compiled as usual. Separately, the assembly code for these functions is compiled, and the resulting object data is transplanted back into the C object. Symbols and relocations are updated as needed to ensure correctness.

Any `.rodata` sections within the assembly code will also be transplanted into the C object.

## Usage

```
mwccgap input.c output.o [ -O4,p -sym on ... ]
```

`mwccgap` supports the following arguments:

### `--mwcc-path` (path)
The path to the MWCC executable, defaults to `mwccpsp.exe`

### `--as-path` (path)
The path to GNU as, defaults to `mipsel-linux-gnu-as`

### `--as-march`
The `-march=` value to pass to GNU as, defaults to `allegrex`

### `--as-mabi`
The `-mabi=` value to pass to GNU as, defaults to `32`

### `--use-wibo`
Whether or not to prefix the call to the MWCC executable with [wibo](https://github.com/decompals/wibo), defaults to false.

### `--wibo-path`
Path to `wibo` (i.e. if `wibo` is not on your path, or you wish to use `wine` instead), defaults to `wibo`.

### `--asm-dir-prefix`
Optional prefix for `INCLUDE_ASM` files.


All additional arguments will be passed to the MWCC executable.


## Limitations

The limitations currently outnumber the features, PRs are very welcome to improve the tool.


## Bugs

This project is in it's infancy and is full of assumptions, and therefore likely riddled with bugs; again PRs are welcome!


## Examples

Projects that use `mwccgap` include:

- [Castlevania: Symphony of the Night Decompilation](https://github.com/Xeeynamo/sotn-decomp)

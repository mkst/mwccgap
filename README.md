# mwccgap AKA "MWCC Global Assembly Processor"

This tool allows for individual functions within a C file to be replaced by assembly code, heavily inspired by [asm-processor](https://github.com/simonlindholm/asm-processor).

The MWCC compiler *does* support including raw assembly within a C file, however all variables and functions must be defined, this makes the traditional [Ship of Theseus](https://en.wikipedia.org/wiki/Ship_of_Theseus) approach to matching decomp rather slow and painful.

Where `asm-processor` uses an `GLOBAL_ASM` pragma, `mwccgap` uses `INCLUDE_ASM` macro as the first project to use `mwccgap` uses `gcc`. In future support might be added to suppport either approach.

Functions that are `INCLUDE_ASM`'d within the C file are expanded to `nops` of the appropriate size and the C file is compiled. These functions are then assembled separately, and the resulting object data is transplanted into the C object. Symbols and relocations are updated as necessary.


## Usage

```
mwccgap input.c output.o
```

`mwccgap` supports the following arguments:

### `--mwcc-path` (path)
The path to the MWCC executable, defaults to `mwccpsp.exe`

### `--as-path` (path)
The path to GNU as, defaults to `mipsel-linux-gnu-as`

### `--use-wibo`
Whether or not to prefix the call to the MWCC executable with [wibo](https://github.com/decompals/wibo), defaults to false.

### `--wibo-path`
Path to `wibo` (i.e. if `wibo` is not on your path, or you wish to use `wine` instead), defaults to `wibo`.


## Limitations

The limitations currently outnumber the features, PRs are very welcome to improve the tool.


## Bugs

This project is in it's infancy and is full of assumptions, and therefore likely riddled with bugs; again PRs are welcome!


## Examples

Projets that use `mwccgap` include:

- [Castlevania: Symphony of the Night Decompilation](https://github.com/Xeeynamo/sotn-decomp)

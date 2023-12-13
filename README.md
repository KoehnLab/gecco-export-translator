# gecco-export-translator

Python script capable of parsing export files created by the [GeCCo](https://github.com/ak-ustutt/GeCCo-public) program and transform it to other
formats.

For parsing the initial export file, the script makes use of a grammar defining the file content's structure and then generates a corresponding parser
using [Lark](https://github.com/lark-parser/lark). The syntax of the grammar file is explained in
[Lark's documentation](https://lark-parser.readthedocs.io/en/latest/grammar.html). Should you want to use the grammar in a separate project, note that
it is [LALR(1)](https://en.wikipedia.org/wiki/LALR_parser) compatible, which allows for very efficient parse algorithms.

After parsing the file, the resulting parse tree (AST - abstract syntax tree) can be interpreted in order to be converted into the desired format.

## Setup

### Dependencies

Install the required dependencies via `pip3 install -r requirements.txt` from the root of this repository.

### PYTHONPATH

In order to use the provided script in the `bin` directory, no setup is required - provided you are using the file structure exactly as given in this
repository.

If you want to relocate the script or want to make use of the packaged functions in your own code, set up your PYTHONPATH environment variable to
include the path to the `packages` directory by adding an entry like the following to your `~/.bashrc`:
```
export PYTHONPATH="$PYTHONPATH:/path/to/this/repo/packages"
```


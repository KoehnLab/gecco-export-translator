# gecco-export-translator

Python script capable of parsing export files created by the [GeCCo](https://github.com/ak-ustutt/GeCCo-public) program and transform it to other
formats.

For parsing the initial export file, the script makes use of a grammar defining the file content's structure and then generates a corresponding parser
using [Lark](https://github.com/lark-parser/lark). The syntax of the grammar file is explained in
[Lark's documentation](https://lark-parser.readthedocs.io/en/latest/grammar.html).

After parsing the file, the resulting parse tree (AST - abstract syntax tree) can be interpreted in order to be converted into the desired format.

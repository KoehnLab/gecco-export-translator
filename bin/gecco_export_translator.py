#!/usr/bin/env python3

from lark import Lark

import os


def main():
    script_dir: str = os.path.dirname(os.path.realpath(__file__))
    grammar_dir = os.path.realpath(os.path.join(script_dir, "..", "grammar"))
    grammar_definition = open(
        os.path.join(grammar_dir, "gecco_export_grammar.peg"), "r"
    ).read()
    parser = Lark(grammar_definition)
    print(parser.parse(" [END]").pretty())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import pe
from pe.operators import Star, Class

import os

script_dir: str = os.path.dirname(os.path.realpath(__file__))


def main():
    grammar_definition = open(
        os.path.join(script_dir, "gecco_export_grammar.peg"), "r"
    ).read()
    grammar = pe.compile(grammar_definition, ignore=Star(Class(" \t\r\v\f")))
    grammar.match(" [END]")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import pe
from pe.operators import Star, Class

import os



def main():
    script_dir: str = os.path.dirname(os.path.realpath(__file__))
    grammar_dir = os.path.realpath(os.path.join(script_dir, "..", "grammar"))
    grammar_definition = open(
        os.path.join(grammar_dir, "gecco_export_grammar.peg"), "r"
    ).read()
    grammar = pe.compile(grammar_definition, ignore=Star(Class(" \t\r\v\f")))
    grammar.match(" [END]")


if __name__ == "__main__":
    main()

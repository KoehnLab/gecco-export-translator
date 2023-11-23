#!/usr/bin/env python3

import pe

import os

script_dir: str = os.path.dirname(os.path.realpath(__file__))

def main():
    grammar = pe.compile(open(os.path.join(script_dir, "gecco_export_grammar.peg"), "r").read())
    grammar.match("[END]")

if __name__ == "__main__":
    main()

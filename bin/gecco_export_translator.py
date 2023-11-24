#!/usr/bin/env python3

from lark import Lark, Transformer

from typing import List

import os
import argparse
from dataclasses import dataclass

@dataclass
class Tensor():
    name: str
    factor: float


@dataclass
class Contraction:
    id: int
    result: Tensor
    operators: List[Tensor]
    super_vertex_association: List[int]

class MyTransformer(Transformer):
    def contraction(self, items):
        print(items)

    def DOUBLE(self, value):
        return float(value)

    def INT(self, value):
        return int(value)



def read_grammar() -> str:
    script_dir: str = os.path.dirname(os.path.realpath(__file__))
    grammar_dir = os.path.realpath(os.path.join(script_dir, "..", "grammar"))
    with open(
        os.path.join(grammar_dir, "gecco_export_grammar.lark"), "r"
    ) as grammar_file:
        grammar = grammar_file.read()

    return grammar

def get_parser(parser: str = "lalr") -> Lark:
    return Lark(read_grammar(), parser=parser)


def main():
    argument_parser = argparse.ArgumentParser(
        description="A script capable of parsing an export file generated via GeCCo and translating it to different formats"
    )
    argument_parser.add_argument("export_file", help="Path to the GeCCo export file that shall be translated")
    argument_parser.add_argument("--format", choices=["tex"], default="tex", help="The desired output format")

    args = argument_parser.parse_args()

    parser = get_parser()
    with open(args.export_file, "r") as export_file:
        contents = export_file.read()
    tree = parser.parse(contents)

    MyTransformer().transform(tree)


if __name__ == "__main__":
    main()

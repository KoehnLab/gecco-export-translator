#!/usr/bin/env python3

from typing import List

import argparse
from importlib.util import find_spec
import sys
import os

if find_spec("gecco_translator") is None:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.join(script_dir, "..", "packages"))

from gecco_translator.ast import Index, TensorElement, Contraction
from gecco_translator.parse import parse


from fractions import Fraction


def index_to_tex(index: Index) -> str:
    base_label = ["o", "v", "a"][index.space]
    return "{}_{}".format(base_label, index.id + 1)


def tensor_to_tex(tensor: TensorElement) -> str:
    tex = tensor.name

    creators: List[str] = []
    annihilators: List[str] = []
    for current_idx_group in tensor.indices:
        creators.extend([index_to_tex(x) for x in current_idx_group.creators])
        annihilators.extend([index_to_tex(x) for x in current_idx_group.annihilators])

    tex += "^{" + " ".join(annihilators) + "}"
    tex += "_{" + " ".join(creators) + "}"

    return tex


def to_tex(contractions: List[Contraction]) -> str:
    tex = ""

    for current in contractions:
        if len(tex) > 0:
            tex += "\n"

        tex += tensor_to_tex(current.result)

        factor = Fraction(str(current.factor))
        if factor < 0:
            factor *= -1
            tex += " -= "
        else:
            tex += " += "

        if factor != 1:
            tex += str(factor) + " "

        for vertex in current.vertices:
            tex += tensor_to_tex(vertex) + " "

    return tex


def main():
    argument_parser = argparse.ArgumentParser(
        description="A script capable of parsing an export file generated via GeCCo and translating it to different formats"
    )
    argument_parser.add_argument(
        "export_file", help="Path to the GeCCo export file that shall be translated"
    )
    argument_parser.add_argument(
        "--format", choices=["tex"], default="tex", help="The desired output format"
    )

    args = argument_parser.parse_args()

    with open(args.export_file, "r") as export_file:
        contents = export_file.read()

    contractions: List[Contraction] = parse(contents)

    # print(contractions)

    if args.format == "tex":
        translated = to_tex(contractions=contractions)
        print(translated)
    else:
        raise RuntimeError("Unsupported target format '{}'".format(args.format))


if __name__ == "__main__":
    main()

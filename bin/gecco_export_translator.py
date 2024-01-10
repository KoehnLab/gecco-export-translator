#!/usr/bin/env python3

from typing import List

import argparse
from importlib.util import find_spec
import sys
import os

if find_spec("gecco_translator") is None:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.join(script_dir, "..", "packages"))

from gecco_translator.ast import Contraction
from gecco_translator.parse import parse
from gecco_translator.translators import to_tex, to_sequant


def main():
    argument_parser = argparse.ArgumentParser(
        description="A script capable of parsing an export file generated via GeCCo and translating it to different formats"
    )
    argument_parser.add_argument(
        "export_file", help="Path to the GeCCo export file that shall be translated"
    )
    argument_parser.add_argument(
        "--format",
        choices=["tex", "sequant"],
        default="tex",
        help="The desired output format",
    )

    args = argument_parser.parse_args()

    with open(args.export_file, "r") as export_file:
        contents = export_file.read()

    contractions: List[Contraction] = parse(contents)

    if args.format == "tex":
        print(to_tex(contractions=contractions))
    elif args.format == "sequant":
        print(to_sequant(contractions=contractions))
    else:
        raise RuntimeError("Unsupported target format '{}'".format(args.format))


if __name__ == "__main__":
    main()

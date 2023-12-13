from typing import List
import os

from lark import Lark

from .ast import Contraction, ASTTransformer


def read_grammar() -> str:
    """Reads the GeCCo export format grammar from disk and returns its contents"""
    file_dir: str = os.path.dirname(os.path.realpath(__file__))
    grammar_dir = os.path.realpath(os.path.join(file_dir, "..", "..", "grammar"))
    with open(
        os.path.join(grammar_dir, "gecco_export_grammar.lark"), "r"
    ) as grammar_file:
        grammar = grammar_file.read()

    return grammar


def get_parser(paring_algorithm: str = "lalr") -> Lark:
    """Constructs a Lark parser object configured to use the selected parsing algorithm"""
    return Lark(read_grammar(), parser=paring_algorithm)


def parse(content: str) -> List[Contraction]:
    """Parses the given content in GeCCo export format and returns the parsed list of contractions"""
    raw_tree = get_parser().parse(content)
    return ASTTransformer().transform(raw_tree)

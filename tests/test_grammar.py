#!/usr/bin/env python3

import unittest
import os
import glob
import logging

from lark import Lark, logger

logger.setLevel(logging.DEBUG)


class TestGrammar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script_dir: str = os.path.dirname(os.path.realpath(__file__))
        grammar_dir: str = os.path.realpath(
            os.path.join(cls.script_dir, "..", "grammar")
        )
        cls.grammar_path = os.path.join(grammar_dir, "gecco_export_grammar.lark")
        with open(cls.grammar_path, "r") as grammar_file:
            cls.grammar = grammar_file.read()

    def test_single_reference_exports(self):
        test_inputs = glob.glob(
            os.path.join(self.script_dir, "single_reference", "*.EXPORT")
        )
        for parser_variant in ["earley", "lalr"]:
            parser = Lark(self.grammar, parser=parser_variant)
            for current_input in test_inputs:
                with open(os.path.join(current_input), "r") as file:
                    content = file.read()
                with self.subTest(
                    "Unable to parse valid export file",
                    parser=parser_variant,
                    file=current_input,
                ):
                    parser.parse(content)

    def test_multi_reference_exports(self):
        test_inputs = glob.glob(
            os.path.join(self.script_dir, "multi_reference", "*.EXPORT")
        )
        for parser_variant in ["earley", "lalr"]:
            parser = Lark(self.grammar, parser=parser_variant)
            for current_input in test_inputs:
                with open(os.path.join(current_input), "r") as file:
                    content = file.read()
                with self.subTest(
                    "Unable to parse valid export file",
                    parser=parser_variant,
                    file=current_input,
                ):
                    parser.parse(content)


if __name__ == "__main__":
    unittest.main()

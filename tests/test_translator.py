#!/usr/bin/env python3

from typing import List

import unittest
from pathlib import Path
import os
import sys
import glob
from importlib.util import find_spec

script_dir: str = os.path.dirname(os.path.realpath(__file__))

if find_spec("gecco_translator") is None:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.join(script_dir, "..", "packages"))

from gecco_translator.translators import to_tex
from gecco_translator.ast import Contraction
from gecco_translator.parse import parse


class TestTranslator(unittest.TestCase):
    def perform_test(self, input_file: str, result_file: str, test_label: str):
        with self.subTest(test_label, input=input_file, expected=result_file):
            contents = Path(input_file).read_text()
            contractions: List[Contraction] = parse(contents)

            output = to_tex(contractions=contractions)
            expected_output = Path(result_file).read_text()

            self.assertEqual(output.strip(), expected_output.strip())

    def test_sr_ccd(self):
        expected_results = glob.glob(
            os.path.join(script_dir, "single_reference", "CCD_*.TRANS")
        )
        inputs = [x.replace("TRANS", "EXPORT") for x in expected_results]

        for export_file, result_file in zip(inputs, expected_results):
            self.perform_test(export_file, result_file, "CCD")

    def test_mr_nevpt2(self):
        expected_results = glob.glob(
            os.path.join(script_dir, "multi_reference", "NEVPT2_*.TRANS")
        )
        inputs = [x.replace("TRANS", "EXPORT") for x in expected_results]

        for export_file, result_file in zip(inputs, expected_results):
            self.perform_test(export_file, result_file, "NEVPT2")


if __name__ == "__main__":
    unittest.main()

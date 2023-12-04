#!/usr/bin/env python3

from lark import Lark, Transformer

from typing import List, Tuple

import os
import argparse
from dataclasses import dataclass


@dataclass
class IndexGroup:
    creators: List[str]
    annihilators: List[str]


@dataclass
class Tensor:
    name: str
    indexing: List[IndexGroup]
    transposed: bool


@dataclass
class Arc:
    first_vertex_idx: int
    second_vertex_idx: int
    indices: IndexGroup


@dataclass
class ExternalArc:
    origin_vertex_idx: int
    result_super_vertex: int
    indices: IndexGroup


@dataclass
class Index:
    id: int
    space: int
    vertex: int
    type: int


@dataclass
class Contraction:
    id: int
    factor: float
    result: Tensor
    super_vertex_association: List[int]
    vertices: List[Tensor]
    arcs: List[Arc]
    external_arcs: List[Arc]
    contraction_indices: List[Index]
    external_indices: List[Index]


class MyTransformer(Transformer):
    def start(self, contractions) -> List[Contraction]:
        return list(contractions)

    def contraction(self, items) -> Contraction:
        (
            contr_id,
            result_tensor,
            factor,
            num_vertices,
            super_vertex_association,
            num_arcs,
            vertices,
            arcs,
            external_arcs,
            contraction_indices,
            external_indices,
        ) = items

        # Transform to 0-based indexing
        assert type(contr_id) == int
        assert contr_id > 0
        contr_id -= 1

        return Contraction(
            id=contr_id,
            factor=factor,
            result=result_tensor,
            super_vertex_association=super_vertex_association,
            vertices=vertices,
            arcs=arcs,
            external_arcs=external_arcs,
            contraction_indices=contraction_indices,
            external_indices=external_indices,
        )

    def result_string(self, parts) -> List[Index]:
        assert len(parts) % 5 == 0
        nIndices = len(parts) // 5

        result_indices: List[Index] = []

        for i in range(nIndices):
            vertex_idx = parts[i]
            idx_type = parts[i + nIndices]
            idx_space = parts[i + 2 * nIndices]
            external = parts[i + 3 * nIndices]
            # This data is duplicated
            vertex_idx2 = parts[i + 4 * nIndices]
            idx_id = parts[i + 5 * nIndices]

            assert vertex_idx == vertex_idx2

            # Transform to 0-based indexing
            assert type(vertex_idx) == int
            assert vertex_idx > 0
            vertex_idx -= 1
            assert type(idx_type) == int
            assert idx_type > 0
            idx_type -= 1
            assert type(idx_space) == int
            assert idx_space > 0
            idx_space -= 1
            assert type(idx_id) == int
            assert idx_id > 0
            idx_id -= 1

            assert type(external) == str
            assert external in ["T", "F"]
            external = True if external == "T" else False

            if external:
                continue

            idx = Index(id=idx_id, space=idx_space, vertex=vertex_idx, type=idx_type)
            result_indices.append(idx)

        assert not None in result_indices
        return result_indices

    def contr_string(self, parts) -> List[Index]:
        assert len(parts) % 6 == 0
        nIndices = len(parts) // 6

        contraction_indices: List[Index] = []

        for i in range(nIndices):
            vertex_idx = parts[i]
            idx_type = parts[i + nIndices]
            idx_space = parts[i + 2 * nIndices]
            external = parts[i + 3 * nIndices]
            arc_idx = parts[i + 4 * nIndices]
            idx_id = parts[i + 5 * nIndices]

            # Transform to 0-based indexing
            assert type(vertex_idx) == int
            assert vertex_idx > 0
            vertex_idx -= 1
            assert type(idx_type) == int
            assert idx_type > 0
            idx_type -= 1
            assert type(idx_space) == int
            assert idx_space > 0
            idx_space -= 1
            assert type(arc_idx) == int
            assert arc_idx > 0
            arc_idx -= 1
            assert type(idx_id) == int
            assert idx_id > 0
            idx_id -= 1

            assert type(external) == str
            assert external in ["T", "F"]
            external = True if external == "T" else False

            if external:
                continue

            idx = Index(id=idx_id, space=idx_space, vertex=vertex_idx, type=idx_type)
            contraction_indices.append(idx)

        assert not None in contraction_indices
        return contraction_indices

    def vertices(self, tensors) -> List[Tensor]:
        return list(tensors)

    def external_arcs(self, parts) -> List[Arc]:
        return self.arcs(parts)

    def arcs(self, parts) -> List[Arc]:
        arcs = list(parts)

        for current in arcs:
            assert type(current) == Arc

        return arcs

    def arc_spec(self, components) -> Arc:
        first_vertex_idx, second_vertex_idx, indexing = components
        assert type(first_vertex_idx) == int
        assert type(second_vertex_idx) == int

        # Transform to 0-based indexing
        assert first_vertex_idx > 0
        assert second_vertex_idx > 0
        first_vertex_idx -= 1
        second_vertex_idx -= 1

        return Arc(
            first_vertex_idx=first_vertex_idx,
            second_vertex_idx=second_vertex_idx,
            indices=indexing,
        )

    def super_vertex(self, spec) -> List[int]:
        vertex_association = list(spec)

        # Transform to 0-based indexing
        for i in range(len(vertex_association)):
            assert type(vertex_association[i]) == int
            assert vertex_association[i] > 0
            vertex_association[i] -= 1

        return vertex_association

    def tensor_spec(self, components) -> Tensor:
        name, transposed, indices = components
        assert transposed in ["T", "F"]
        transposed = True if transposed == "T" else False

        return Tensor(name=name, indexing=indices, transposed=transposed)

    def index_spec(self, spec) -> List[IndexGroup]:
        assert len(spec) % 2 == 0
        groups: List[IndexGroup] = []
        for i in range(0, len(spec), 2):
            creators = list(spec[i]) if spec[i] is not None else []
            annihilators = list(spec[i + 1]) if spec[i + 1] is not None else []
            groups.append(IndexGroup(creators=creators, annihilators=annihilators))

        return groups

    def factor(self, factors) -> float:
        external, sign, contraction_factor = factors
        return external * sign * contraction_factor

    def DOUBLE(self, value) -> float:
        return float(value)

    def INT(self, value) -> int:
        return int(value)

    def ID(self, characters) -> str:
        return "".join(characters)


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
    argument_parser.add_argument(
        "export_file", help="Path to the GeCCo export file that shall be translated"
    )
    argument_parser.add_argument(
        "--format", choices=["tex"], default="tex", help="The desired output format"
    )

    args = argument_parser.parse_args()

    parser = get_parser()
    with open(args.export_file, "r") as export_file:
        contents = export_file.read()
    tree = parser.parse(contents)

    contractions: List[Contraction] = MyTransformer().transform(tree)
    print(contractions)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from lark import Lark, Transformer

from typing import List, Tuple

import os
import argparse
from dataclasses import dataclass
from fractions import Fraction


@dataclass
class IndexSpaces:
    creators: List[int]
    annihilators: List[int]


@dataclass
class Operator:
    name: str
    indexing: List[IndexSpaces]
    transposed: bool


@dataclass
class Index:
    id: int
    space: int
    vertex: int
    type: int


@dataclass
class IndexGroup:
    creators: List[Index]
    annihilators: List[Index]


@dataclass
class TensorElement:
    name: str
    indices: List[IndexGroup]
    transposed: bool


@dataclass
class Arc:
    first_vertex_idx: int
    second_vertex_idx: int
    indices: IndexSpaces


@dataclass
class ExternalArc:
    origin_vertex_idx: int
    result_super_vertex: int
    indices: IndexSpaces


@dataclass
class Contraction:
    id: int
    factor: float
    result: TensorElement
    super_vertex_association: List[int]
    vertices: List[TensorElement]
    arcs: List[Arc]
    external_arcs: List[Arc]
    contraction_indices: List[Index]
    external_indices: List[Index]


def argsort(sequence):
    return sorted(range(len(sequence)), key=sequence.__getitem__)


def add_indices(
    operators: List[Operator], vertex_ids: List[int], indices: List[Index]
) -> TensorElement:
    assert len(operators) == len(vertex_ids)
    # Assume all operators belong to the same super vertex and thus have the same name
    assert all(x.name == operators[0].name for x in operators)

    print("Op name: ", operators[0].name)

    tensor_indices: List[IndexGroup] = []

    for i in range(len(operators)):
        current_op = operators[i]
        current_vertex_id = vertex_ids[i]

        current_indices = [x for x in indices if x.vertex == current_vertex_id]
        creators = [x for x in current_indices if x.type == 0]
        annihilators = [x for x in current_indices if x.type == 1]
        assert len(creators) + len(annihilators) == len(current_indices)

        assert len(current_op.indexing) == 1

        spaces: IndexSpaces = current_op.indexing[0]

        assert len(spaces.creators) == len(creators)
        assert len(spaces.annihilators) == len(annihilators)
        assert all(
            creators[i].space == spaces.creators[i] for i in range(len(creators))
        )
        print(annihilators)
        print(spaces.annihilators)
        print()
        assert all(
            annihilators[i].space == spaces.annihilators[i]
            for i in range(len(annihilators))
        )

        # In GeCCo the index pairing (which indices belong to same particle) goes from the outside
        # to the inside, e.g. 12|21, but we would like a column-like association where same-particle
        # indices stand on top of each other when splitting between creators and annihilators.
        # Therefore, we have to reverse the order of annihilators to get e.g. 12|12
        annihilators.reverse()

        tensor_indices.append(IndexGroup(creators=creators, annihilators=annihilators))

    return TensorElement(
        name=operators[0].name,
        transposed=operators[0].transposed,
        indices=tensor_indices,
    )


class MyTransformer(Transformer):
    def start(self, contractions) -> List[Contraction]:
        return list(contractions)

    def contraction(self, items) -> Contraction:
        (
            contr_id,
            result_op,
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

        n_vertices, n_operators = num_vertices
        n_arcs, n_xarcs = num_arcs

        assert len(vertices) == n_vertices
        assert len(set(super_vertex_association)) == n_operators
        assert len(arcs) == n_arcs
        assert len(external_arcs) == n_xarcs

        # Transform to 0-based indexing
        assert type(contr_id) == int
        assert contr_id > 0
        contr_id -= 1

        print("Contraction #", contr_id + 1)

        contracted_tensors: List[TensorElement] = []

        # 1. Identify all vertices belonging to a single super-vertex
        # 2. Feed these vertices together into add_indices to yield indexed TensorElements
        vertex_order = argsort(super_vertex_association)
        vertex_iter = iter(vertex_order)
        for i in vertex_iter:
            # Find vertices that belong to the same super vertex
            super_vertex = super_vertex_association[i]
            vertex_ids = [i]
            vertex_group = [vertices[i]]
            while (
                len(super_vertex_association) > i + 1
                and super_vertex_association[i + 1] == super_vertex
            ):
                i = next(vertex_iter)
                vertex_ids.append(i)
                vertex_group.append(vertices[i])

            tensor = add_indices(
                indices=contraction_indices,
                vertex_ids=vertex_ids,
                operators=vertex_group,
            )
            contracted_tensors.append(tensor)

        # Note: result_op can consist of multiple vertices itself
        # -> split into individual vertices before also feeding to add_indices
        if len(result_op.indexing) > 1:
            result_vertices = []
            result_super_vertices = []
        else:
            result_vertices = [result_op]
            result_super_vertices = [0]
        result_tensor = add_indices(
            operators=result_vertices,
            vertex_ids=result_super_vertices,
            indices=external_indices,
        )

        return Contraction(
            id=contr_id,
            factor=factor,
            result=result_tensor,
            super_vertex_association=super_vertex_association,
            vertices=contracted_tensors,
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
            # This data is duplicated
            vertex_idx2 = parts[i + 3 * nIndices]
            idx_id = parts[i + 4 * nIndices]

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

            idx = Index(id=idx_id, space=idx_space, vertex=vertex_idx, type=idx_type)
            result_indices.append(idx)

        assert not None in result_indices
        assert len(result_indices) == nIndices

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

            # TODO: Do we need the external tag somewhere?
            # also beware that arc_idx is result_vert_idx if external == True

            idx = Index(id=idx_id, space=idx_space, vertex=vertex_idx, type=idx_type)
            contraction_indices.append(idx)

        assert not None in contraction_indices
        return contraction_indices

    def vertices(self, operators) -> List[Operator]:
        return list(operators)

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

    def num_arcs(self, parts) -> Tuple[int, int]:
        num_arcs, num_xarcs = parts
        assert type(num_arcs) is int
        assert type(num_xarcs) is int
        return (num_arcs, num_xarcs)

    def num_vertices(self, parts) -> Tuple[int, int]:
        num_vertices, num_operators = parts
        assert type(num_vertices) is int
        assert type(num_operators) is int
        return (num_vertices, num_operators)

    def super_vertex(self, spec) -> List[int]:
        vertex_association = list(spec)

        # Transform to 0-based indexing
        for i in range(len(vertex_association)):
            assert type(vertex_association[i]) == int
            assert vertex_association[i] > 0
            vertex_association[i] -= 1

        return vertex_association

    def operator_spec(self, components) -> Operator:
        name, transposed, indices = components
        assert transposed in ["T", "F"]
        transposed = True if transposed == "T" else False

        if transposed:
            # For transposed operators we have to exchange creator and annihilator spaces
            for i in range(len(indices)):
                current_group: IndexSpaces = indices[i]
                current_group.creators, current_group.annihilators = (
                    current_group.annihilators,
                    current_group.creators,
                )
                indices[i] = current_group

        return Operator(name=name, indexing=indices, transposed=transposed)

    def space_groups(self, spec) -> List[IndexSpaces]:
        name_to_id = {
            "H": 0,  # occupied
            "P": 1,  # virtual
            "V": 2,  # active
        }

        assert len(spec) % 2 == 0
        groups: List[IndexSpaces] = []
        for i in range(0, len(spec), 2):
            creators = list(spec[i]) if spec[i] is not None else []
            annihilators = list(spec[i + 1]) if spec[i + 1] is not None else []

            # Convert index spaces from string to numeric representation
            creators = [name_to_id[x] for x in creators]
            annihilators = [name_to_id[x] for x in annihilators]

            groups.append(IndexSpaces(creators=creators, annihilators=annihilators))

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

    parser = get_parser()
    with open(args.export_file, "r") as export_file:
        contents = export_file.read()
    tree = parser.parse(contents)

    contractions: List[Contraction] = MyTransformer().transform(tree)

    # print(contractions)

    if args.format == "tex":
        translated = to_tex(contractions=contractions)
        print(translated)
    else:
        raise RuntimeError("Unsupported target format '{}'".format(args.format))


if __name__ == "__main__":
    main()

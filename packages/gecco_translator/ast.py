from typing import List, Tuple
from dataclasses import dataclass

from lark import Transformer


@dataclass
class IndexSpaces:
    creators: List[int]
    annihilators: List[int]


@dataclass
class ResultOperator:
    name: str
    vertices: List[IndexSpaces]
    transposed: bool


@dataclass
class OperatorVertex:
    name: str
    spaces: IndexSpaces
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
    vertex_indices: List[IndexGroup]
    transposed: bool


@dataclass
class Arc:
    first_vertex_idx: int
    second_vertex_idx: int
    contracted_spaces: IndexSpaces


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
    tensors: List[TensorElement]
    contractions: List[Arc]
    external_contractions: List[ExternalArc]
    contraction_indices: List[Index]
    external_indices: List[Index]


def argsort(sequence) -> List[int]:
    """Returns a list of indices into the provided sequence such that accessing the indexed elements in order will result
    in accessing the sequence in an ordered (sorted) way. This is a pure Python reimplementation of NumPy's argsort functionality.
    """
    return sorted(range(len(sequence)), key=sequence.__getitem__)


def first_index_of_space(indices: List[Index], space: int, start: int = 0) -> int:
    """Gets the index of the first Index object in indices that belongs to the given index space. start defines
    from which starting offset on to consider Index objects inside indices."""
    for i in range(start, len(indices)):
        if indices[i].space == space:
            return i

    raise ValueError(
        "No index belongs to space {} for an offset >= {}".format(space, start)
    )


def order_indices_by_space(indices: List[Index], spaces: List[int]) -> List[Index]:
    """Orders the Index objects inside indices in such a way that their associated index spaces match the order
    of spaces as provided in the spaces list. Relative order of Index objects of the same space is retained.
    """
    assert len(indices) == len(spaces)

    for i in range(len(indices)):
        if indices[i].space == spaces[i]:
            # Index matches space -> keep it where it is
            continue

        # Space of i-th index != i-th space -> insert first matching index instead
        matching_index_idx = first_index_of_space(
            indices=indices, space=spaces[i], start=i
        )
        assert matching_index_idx > i
        indices.insert(i, indices[matching_index_idx])
        # Delete the index that we have inserted at position i
        del indices[matching_index_idx + 1]

    return indices


def add_indices(
    operator_vertices: List[OperatorVertex], vertex_ids: List[int], indices: List[Index]
) -> TensorElement:
    assert len(operator_vertices) == len(vertex_ids)
    # Assume all operators belong to the same super vertex and thus have the same name
    assert all(x.name == operator_vertices[0].name for x in operator_vertices)

    tensor_indices: List[IndexGroup] = []

    for i in range(len(operator_vertices)):
        current_op = operator_vertices[i]
        current_vertex_id = vertex_ids[i]

        current_indices = [x for x in indices if x.vertex == current_vertex_id]
        creators = [x for x in current_indices if x.type == 0]
        annihilators = [x for x in current_indices if x.type == 1]
        assert len(creators) + len(annihilators) == len(current_indices)

        spaces: IndexSpaces = current_op.spaces

        assert len(spaces.creators) == len(creators)
        assert len(spaces.annihilators) == len(annihilators)

        creators = order_indices_by_space(indices=creators, spaces=spaces.creators)
        annihilators = order_indices_by_space(
            indices=annihilators, spaces=spaces.annihilators
        )

        assert all(
            creators[i].space == spaces.creators[i] for i in range(len(creators))
        )
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
        name=operator_vertices[0].name,
        transposed=operator_vertices[0].transposed,
        vertex_indices=tensor_indices,
    )


class ASTTransformer(Transformer):
    def start(self, contractions) -> List[Contraction]:
        return list(contractions)

    def contraction(
        self,
        items: Tuple[
            int,
            ResultOperator,
            float,
            Tuple[int, int],
            List[int],
            Tuple[int, int],
            List[OperatorVertex],
            List[Arc],
            List[ExternalArc],
            List[Index],
            List[Index],
        ],
    ) -> Contraction:
        (
            contr_id,
            result_op,
            factor,
            vertex_counters,
            super_vertex_association,
            arc_counters,
            vertices,
            arcs,
            external_arcs,
            contraction_indices,
            external_indices,
        ) = items

        n_vertices, n_operators = vertex_counters
        n_arcs, n_xarcs = arc_counters

        assert len(vertices) == n_vertices
        assert len(set(super_vertex_association)) == n_operators
        assert len(arcs) == n_arcs
        assert len(external_arcs) == n_xarcs

        # Transform to 0-based indexing
        assert type(contr_id) == int
        assert contr_id > 0
        contr_id -= 1

        contracted_tensors: List[TensorElement] = []

        # 1. Identify all vertices belonging to a single super-vertex
        # 2. Feed these vertices together into add_indices to yield indexed TensorElements
        vertex_order = argsort(super_vertex_association)
        i = 0
        while i < len(vertex_order):
            idx = vertex_order[i]
            # Find vertices that belong to the same super vertex
            super_vertex = super_vertex_association[idx]
            vertex_ids = [idx]
            vertex_group = [vertices[idx]]
            while (
                len(vertex_order) > i + 1
                and super_vertex_association[vertex_order[i + 1]] == super_vertex
            ):
                i += 1
                idx = vertex_order[i]
                vertex_ids.append(idx)
                vertex_group.append(vertices[idx])

            tensor = add_indices(
                indices=contraction_indices,
                vertex_ids=vertex_ids,
                operator_vertices=vertex_group,
            )
            contracted_tensors.append(tensor)

            i += 1

        assert len(contracted_tensors) == n_operators

        # Note: result_op can consist of multiple vertices itself
        # -> split into individual vertices before also feeding to add_indices
        result_vertices: List[OperatorVertex] = []
        result_super_vertices: List[int] = []
        for i, current_space_group in enumerate(result_op.vertices):
            result_vertices.append(
                OperatorVertex(
                    name=result_op.name,
                    spaces=current_space_group,
                    transposed=result_op.transposed,
                )
            )
            result_super_vertices.append(i)

        result_tensor = add_indices(
            operator_vertices=result_vertices,
            vertex_ids=result_super_vertices,
            indices=external_indices,
        )

        return Contraction(
            id=contr_id,
            factor=factor,
            result=result_tensor,
            tensors=contracted_tensors,
            contractions=arcs,
            external_contractions=external_arcs,
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

            # Beware that arc_idx is result_vert_idx if external == True

            idx = Index(id=idx_id, space=idx_space, vertex=vertex_idx, type=idx_type)
            contraction_indices.append(idx)

        assert not None in contraction_indices
        return contraction_indices

    def vertices(self, operators) -> List[OperatorVertex]:
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
            contracted_spaces=indexing,
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

    def result_spec(self, components) -> ResultOperator:
        name, transposed, vertices = components
        assert transposed in ["T", "F"]
        transposed = True if transposed == "T" else False

        if transposed:
            # For transposed operators we have to exchange creator and annihilator spaces
            for i in range(len(vertices)):
                current_group: IndexSpaces = vertices[i]
                current_group.creators, current_group.annihilators = (
                    current_group.annihilators,
                    current_group.creators,
                )
                vertices[i] = current_group

        return ResultOperator(name=name, vertices=vertices, transposed=transposed)

    def vertex(self, components) -> OperatorVertex:
        name, transposed, spaces = components
        assert transposed in ["T", "F"]
        transposed = True if transposed == "T" else False

        if transposed:
            # For transposed operators we have to exchange creator and annihilator spaces
            spaces.creators, spaces.annihilators = (
                spaces.annihilators,
                spaces.creators,
            )

        return OperatorVertex(name=name, spaces=spaces, transposed=transposed)

    name_to_id = {
        "H": 0,  # occupied
        "P": 1,  # virtual
        "V": 2,  # active
    }

    def index_space_group(self, spec) -> IndexSpaces:
        assert len(spec) == 2
        creators = list(spec[0]) if spec[0] is not None else []
        annihilators = list(spec[1]) if spec[1] is not None else []

        # Convert index spaces from string to numeric representation
        creators = [self.name_to_id[x] for x in creators]
        annihilators = [self.name_to_id[x] for x in annihilators]

        return IndexSpaces(creators=creators, annihilators=annihilators)

    def result_vertex_spaces(self, spec) -> List[IndexSpaces]:
        assert len(spec) % 2 == 0
        groups: List[IndexSpaces] = []
        for i in range(0, len(spec), 2):
            creators = list(spec[i]) if spec[i] is not None else []
            annihilators = list(spec[i + 1]) if spec[i + 1] is not None else []

            # Convert index spaces from string to numeric representation
            creators = [self.name_to_id[x] for x in creators]
            annihilators = [self.name_to_id[x] for x in annihilators]

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

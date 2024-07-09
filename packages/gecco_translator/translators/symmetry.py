from typing import List, Tuple, Optional, Set

from itertools import product
import copy

from gecco_translator.ast import Contraction, Index, TensorElement


def strip_index(idx: Index) -> Index:
    return Index(id=idx.id, space=idx.space, type=idx.type, vertex=-1)


def strip_tensor(tensor: TensorElement) -> TensorElement:
    for i in range(len(tensor.vertex_indices)):
        current = tensor.vertex_indices[i]
        current.creators = [strip_index(x) for x in current.creators]
        current.annihilators = [strip_index(x) for x in current.annihilators]
        tensor.vertex_indices[i] = current

    return tensor


def strip_contraction(contr: Contraction) -> Contraction:
    contr_copy = copy.deepcopy(contr)

    contr_copy.result = strip_tensor(contr_copy.result)
    for i in range(len(contr_copy.tensors)):
        contr_copy.tensors[i] = strip_tensor(contr_copy.tensors[i])

    return contr_copy


def find_index(idx: Index, tensors: List[TensorElement]) -> Tuple[int, int]:
    for i in range(len(tensors)):
        current_tensor = tensors[i]

        for k in range(len(current_tensor.vertex_indices)):
            current_vertex = current_tensor.vertex_indices[k]

            if idx.type == 0:
                found = idx in current_vertex.creators
            else:
                assert idx.type == 1
                found = idx in current_vertex.annihilators

            if found:
                return (i, k)

    raise ValueError(
        "Unable to find {} in the set of given tensor elements".format(idx)
    )


def indices_from_different_vertices(
    indices: List[Index], tensors: List[TensorElement]
) -> List[Tuple[Index, Index]]:
    idx_pairs: List[Tuple[Index, Index]] = []

    # Iterate over all pairs of indices
    for i in range(len(indices)):
        first = indices[i]
        first_origin = find_index(idx=first, tensors=tensors)
        for j in range(i + 1, len(indices)):
            second = indices[j]
            second_origin = find_index(idx=second, tensors=tensors)

            if first.space != second.space:
                continue

            if first_origin != second_origin:
                idx_pairs.append((first, second))

    return idx_pairs


def condense_symmetrizations(symmetrizations: List[Set[Index]]) -> List[Set[Index]]:
    i = 0
    while i < len(symmetrizations):
        current_symm = symmetrizations[i]
        redo_iteration = False
        for j in range(i + 1, len(symmetrizations)):
            if len(symmetrizations[j].intersection(current_symm)) > 0:
                new_indices = symmetrizations[j].difference(current_symm)
                old_indices = current_symm.difference(symmetrizations[j])

                required_symmetrizations = [
                    set(x) for x in product(new_indices, old_indices)
                ]

                if all(x in symmetrizations for x in required_symmetrizations):
                    current_symm |= new_indices
                    redo_iteration = True

                    symmetrizations = [
                        x for x in symmetrizations if x not in required_symmetrizations
                    ]
                    break

        if not redo_iteration:
            i += 1

    return symmetrizations


def get_required_symmetrizations(
    orig_contraction: Contraction,
) -> Tuple[List[Set[Index]], List[Set[Index]]]:
    # Ensure all indices only differ in relevant properties
    contraction = strip_contraction(orig_contraction)

    # All indices of the same type (creator/annihilator) are meant/required to be antisymmetric under pairwise permutations
    creator_symmetrizations: List[Set[Index]] = []
    annihilator_symmetrizations: List[Set[Index]] = []

    for current_indices in contraction.result.vertex_indices:
        creator_symmetrizations.extend(
            [
                set(x)
                for x in indices_from_different_vertices(
                    indices=current_indices.creators, tensors=contraction.tensors
                )
            ]
        )
        annihilator_symmetrizations.extend(
            [
                set(x)
                for x in indices_from_different_vertices(
                    indices=current_indices.annihilators, tensors=contraction.tensors
                )
            ]
        )

    condense_symmetrizations(creator_symmetrizations)
    condense_symmetrizations(annihilator_symmetrizations)

    return (creator_symmetrizations, annihilator_symmetrizations)

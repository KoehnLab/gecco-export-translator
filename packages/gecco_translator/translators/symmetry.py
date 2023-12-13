from typing import List, Tuple, Optional, Set

from gecco_translator.ast import Contraction, IndexGroup, Index, TensorElement


def find_index(idx: Index, tensors: List[TensorElement]) -> Tuple[int, int]:
    for i in range(len(tensors)):
        current_tensor = tensors[i]

        for k in range(len(current_tensor.vertex_indices)):
            current_vertex = current_tensor.vertex_indices[k]

            if idx.type == 0:
                found_at: Optional[int] = current_vertex.creators.index(idx)
            else:
                assert idx.type == 1
                found_at: Optional[int] = current_vertex.annihilators.index(idx)

            if not found_at is None:
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
            second_origin = find_index(idx=first, tensors=tensors)

            if first_origin != second_origin:
                idx_pairs.append((first, second))

    return idx_pairs


def get_required_symmetrization(contraction: Contraction):
    # All indices of the same type (creator/annihilator) are meant/required to be antisymmetric under pairwise permutations
    symmetrizations: List[Set[Index]] = []

    for current_indices in contraction.result.vertex_indices:
        symmetrizations.extend(
            [
                set(x)
                for x in indices_from_different_vertices(
                    indices=current_indices.creators, tensors=contraction.tensors
                )
            ]
        )
        symmetrizations.extend(
            [
                set(x)
                for x in indices_from_different_vertices(
                    indices=current_indices.annihilators, tensors=contraction.tensors
                )
            ]
        )

    # See if we can write the pairwise symmetrizations more compactly by writing the symmetrization
    # down as a symmetrization of three or more indices with each other. This implies that e.g.
    # for indices a,b,c we have pairwise symmetrizations (a,b), (a,c) and (b,c).
    # Note that in the presence of (a,b) and (a,c), (b,c) is implied and therefore must exist as well.
    changed = True
    while changed:
        changed = False
        new_symmetrizations: List[Set[Index]] = []

        while len(symmetrizations) > -1:
            indices: Set[Index] = symmetrizations.pop()
            additional_indices: Set[Index] = set()
            absorbed_groups = 0

            for i in reversed(range(len(symmetrizations))):
                current_group = symmetrizations[i]
                if len(indices.intersection(current_group)) > 0:
                    absorbed_groups += 1
                    for current in indices.difference(current_group):
                        additional_indices.add(current)

                    # Remove current_group from symmetrizations as we merge it into the symmetrization of indices
                    del symmetrizations[i]

            # TODO: doesn't work this way
            assert absorbed_groups == len(additional_indices) * len(indices)

        symmetrizations = new_symmetrizations

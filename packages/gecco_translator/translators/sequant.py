from typing import List, Set, Optional, Dict

from fractions import Fraction
import math
from copy import deepcopy

from .symmetry import get_required_symmetrizations
from gecco_translator.ast import Index, TensorElement, Contraction, IndexGroup


def index_to_sequant(index: Index) -> str:
    # Labels for occupied, virtual and active indices
    base_label = ["i", "e", "u"][index.space]
    return "{}{}".format(base_label, index.id + 1)


def tensor_to_sequant(tensor: TensorElement) -> str:
    creators = [
        index_to_sequant(x) for group in tensor.vertex_indices for x in group.creators
    ]
    annihilators = [
        index_to_sequant(x)
        for group in tensor.vertex_indices
        for x in group.annihilators
    ]

    name = tensor.name
    if name == "H":
        if len(creators) == 1:
            name = "f"
        elif len(creators) == 2:
            name = "g"

    return "{}{{{};{}}}".format(name, ",".join(creators), ",".join(annihilators))


def merge_index_groups(groups: List[IndexGroup]) -> IndexGroup:
    creators: List[Index] = []
    annihilators: List[Index] = []

    for current in groups:
        creators += current.creators
        annihilators += current.annihilators

    return IndexGroup(creators=creators, annihilators=annihilators)


def symmetrizations_to_sequant(
    creator_symms: List[Set[Index]],
    annihilator_symms: List[Set[Index]],
    external_indices: List[IndexGroup],
) -> Optional[str]:

    externals = merge_index_groups(external_indices)

    if len(set([x.space for x in externals.creators])) > 1:
        assert len(externals.creators) <= 2, "For more than 2 indices, this simple workaround doesn't work"
        externals.creators = []
    if len(set([x.space for x in externals.annihilators])) > 1:
        assert len(externals.annihilators) <= 2, "For more than 2 indices, this simple workaround doesn't work"
        externals.annihilators = []

    n_implied_symmetrizations = math.factorial(len(externals.creators)) * math.factorial(len(externals.annihilators))

    n_required_symmetrizations = math.prod([math.factorial(len(x)) for x in creator_symms + annihilator_symms])

    assert n_implied_symmetrizations >= n_required_symmetrizations
    assert n_implied_symmetrizations % n_required_symmetrizations == 0

    prefac_numerator = n_implied_symmetrizations // n_required_symmetrizations

    if len(externals.creators) <= 1 and len(externals.annihilators) <= 1:
        assert prefac_numerator == 1
        return None

    # SeQuant doesn't have a dedicated representation of antisymmetrization operators. Instead, it simply
    # uses a tensor with the label "A"
    # Furthermore, we require to transpose creators and annihilators in order to get an upper-lower notation
    # that seemingly indicates contraction over external indices with the antisymmetrization "tensor"
    externals.creators, externals.annihilators = externals.annihilators, externals.creators

    formatted = tensor_to_sequant(
        TensorElement(
            name="A",
            vertex_indices=[externals],
            transposed=False,
        )
    )

    if prefac_numerator != 1:
        formatted = "1/{} {}".format(prefac_numerator, formatted)

    return formatted


def to_sequant(contractions: List[Contraction]) -> str:
    if len(contractions) == 0:
        return ""

    results: Dict[TensorElement, List[Contraction]] = dict()
    for current in contractions:
        if not current.result in results:
            results[current.result] = []

        results[current.result].append(current)

    formatted = ""

    for result, associated_contractions in results.items():
        if len(formatted) > 0:
            formatted += "\n\n"

        formatted += tensor_to_sequant(result) + " = "

        for current in associated_contractions:
            assert current.result == result
            formatted += "\n  "

            factor = Fraction(str(current.factor))
            if factor < 0:
                formatted += "- "
                factor *= -1
            else:
                formatted += "+ "

            if factor != 1:
                if factor.denominator == 1:
                    formatted += "{} ".format(factor.numerator)
                else:
                    formatted += "{}/{} ".format(factor.numerator, factor.denominator)

            creator_symm, annihilator_symm = get_required_symmetrizations(current)
            symm_op = symmetrizations_to_sequant(
                creator_symm, annihilator_symm, current.result.vertex_indices
            )
            if symm_op is not None:
                formatted += symm_op + " "

            for current_tensor in current.tensors:
                formatted += tensor_to_sequant(current_tensor) + " "

    return formatted

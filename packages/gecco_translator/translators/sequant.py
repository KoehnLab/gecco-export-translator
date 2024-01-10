from typing import List, Set, Optional

from fractions import Fraction
import math

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
    return "{}{{{};{}}}".format(tensor.name, ",".join(creators), ",".join(annihilators))


def symmetrizations_to_sequant(
    creator_symms: List[Set[Index]],
    annihilator_symms: List[Set[Index]],
    external_indices: List[IndexGroup],
) -> Optional[str]:
    if len(external_indices) == 0 or (
        len(external_indices) == 1
        and len(external_indices[0].creators) == 0
        and len(external_indices[0].annihilators) == 0
    ):
        return None

    created_symmetrizations = 1
    for group in external_indices:
        created_symmetrizations *= math.factorial(len(group.creators))
        created_symmetrizations *= math.factorial(len(group.annihilators))

    required_symmetrizations = 1
    for current_set in creator_symms:
        required_symmetrizations *= math.factorial(len(current_set))
    for current_set in annihilator_symms:
        required_symmetrizations *= math.factorial(len(current_set))

    assert created_symmetrizations >= required_symmetrizations
    assert created_symmetrizations % required_symmetrizations == 0

    prefac_numerator = created_symmetrizations // required_symmetrizations

    # SeQuant doesn't have a dedicated representation of antisymmetrization operators. Instead, it simply
    # uses a tensor with the label "A"
    formatted = tensor_to_sequant(
        TensorElement(
            name="A",
            vertex_indices=external_indices,
            transposed=False,
        )
    )

    if prefac_numerator != 1:
        formatted = "1/{} {}".format(prefac_numerator, formatted)

    return formatted


def to_sequant(contractions: List[Contraction]) -> str:
    formatted = ""

    for current in contractions:
        if len(formatted) > 0:
            formatted += "\n"

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

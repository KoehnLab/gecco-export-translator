from typing import List, Optional, Set

from fractions import Fraction

from .symmetry import get_required_symmetrizations

from gecco_translator.ast import Index, TensorElement, Contraction


def index_to_tex(index: Index) -> str:
    base_label = ["o", "v", "a"][index.space]
    return "{}_{}".format(base_label, index.id + 1)


def tensor_to_tex(tensor: TensorElement) -> str:
    tex = tensor.name

    creators: List[str] = []
    annihilators: List[str] = []
    for current_idx_group in tensor.vertex_indices:
        creators.extend([index_to_tex(x) for x in current_idx_group.creators])
        annihilators.extend([index_to_tex(x) for x in current_idx_group.annihilators])

    tex += "^{" + " ".join(annihilators) + "}"
    tex += "_{" + " ".join(creators) + "}"

    return tex


def symmetrization_to_idx_seq(symms: List[Set[Index]]) -> List[str]:
    seq: List[str] = []
    for current_set in symms:
        indices = list(current_set)
        indices.sort(key=lambda x: (x.space, x.id))
        seq.append(" ".join(index_to_tex(x) for x in indices))

    return seq


def symmetrizations_to_tex(
    creator_symms: List[Set[Index]], annihilator_symms: List[Set[Index]]
) -> Optional[str]:
    if len(creator_symms) == 0 and len(annihilator_symms) == 0:
        return None

    return r"\hat{{\mathcal{{A}}}}^{{ {} }}_{{ {} }}".format(
        "; ".join(symmetrization_to_idx_seq(annihilator_symms)),
        "; ".join(symmetrization_to_idx_seq(creator_symms)),
    )


def to_tex(contractions: List[Contraction]) -> str:
    tex = ""

    for current in contractions:
        if len(tex) > 0:
            tex += "\n"

        tex += tensor_to_tex(current.result)

        factor = Fraction(str(current.factor))
        tex += r" \leftarrow "
        if factor < 0:
            factor *= -1
            tex += " - "
        else:
            tex += " + "

        if factor != 1:
            if factor.denominator == 1:
                tex += str(factor.numerator)
            else:
                tex += r"\frac{{{}}}{{{}}}".format(factor.numerator, factor.denominator)
            tex += " "

        creator_symm, annihilator_symm = get_required_symmetrizations(current)
        symm_op = symmetrizations_to_tex(creator_symm, annihilator_symm)
        if symm_op is not None:
            tex += symm_op + " "

        for current_tensor in current.tensors:
            tex += tensor_to_tex(current_tensor) + " "

    return tex

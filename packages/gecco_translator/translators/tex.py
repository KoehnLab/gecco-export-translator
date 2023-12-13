from typing import List

from fractions import Fraction

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

        for current_tensor in current.tensors:
            tex += tensor_to_tex(current_tensor) + " "

    return tex


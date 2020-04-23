"""
"""
import torch
import numpy as np
from torch import Tensor
from functools import partial
from typing import Callable

from ..core import timeit, idxs_2d_to_1d
from ..som import Som
from ..interp import mean_quantization_err, topologic_err, codebook_err


__all__ = [
    "SomLoss",
    "BackwardRedirectTensor",
]


class SomLoss(Callable):
    "Wraps a loss function, passing it the som module."

    def __init__(self, loss_fn: Callable, som: Som, **kwargs) -> None:
        self.loss_fn = partial(loss_fn, som=som, **kwargs)
        self.som = som

    def __call__(self, *args, **kwargs) -> Tensor:
        "Calls the underlying `loss_fn` and wraps the result in a `BackwardRedirectTensor`."
        return BackwardRedirectTensor(self.loss_fn(*args, **kwargs), self.som.backward)


class BackwardRedirectTensor(Tensor):
    "A Tensor that calls a custom function instead of PyTorch's `backward`."
    @staticmethod
    def __new__(cls, x: Tensor, redir_fn, *args, **kwargs):
        return super().__new__(cls, x.cpu().numpy(), *args, **kwargs)

    def __init__(self, x: Tensor, redir_fn):
        super().__init__()
        self.redir_fn = redir_fn

    def backward(self, gradient=None, retain_graph=None, create_graph=False):
        self.redir_fn()

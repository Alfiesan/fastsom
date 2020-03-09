"""
This module mimics Fastai dataset utilities for unsupervised data.

"""
from typing import Union
from torch import Tensor
import torch

from .normalizers import Normalizer, get_normalizer


def batch_slice(bs: int, maximum: int) -> slice:
    "Generator function. Generates contiguous slices of size `bs`"
    curr = 0
    while True:
        yield slice(curr, curr+bs)
        # Restart from 0 if max has been reached; advance to next batch otherwise
        curr = 0 if curr+bs > maximum or curr+bs*2 > maximum else curr + bs


def random_batch_slice(bs: int, maximum: int) -> Tensor:
    "Generator function. Generates random slices up to `max_iters` times"
    base = torch.zeros(bs)
    while True:
        # Fill `base` with uniform data
        yield base.uniform_(0, maximum).long()


def pct_split(x: Tensor, pct: float = 0.2):
    "Splits a dataset in `train` and `valid` by using `pct`."
    sep = int(x.shape[0] * (1 - pct))
    return x[:sep], x[sep:]


class UnsupervisedDataset():
    "Represents a dataset without targets."

    def __init__(
            self, train: Tensor,
            valid: Union[Tensor, float] = 0.2,
            bs: int = 64,
            normalizer: Union[Normalizer, str] = 'minmax',
            random_batching: bool = False, shuffle: bool = False):
        if isinstance(valid, float):
            self.train, self.valid = pct_split(train, pct=valid)
        else:
            self.train, self.valid = train, valid
        self.bs = bs
        self.use_cuda = torch.cuda.is_available()
        # Move train and validation datasets to this dataset's device
        self.train = self._to_device(self.train)
        self.valid = self._to_device(self.valid)
        # Initialize the normalizer
        self.normalizer = self._get_normalizer(normalizer)
        # Save random batching option (accessed by `Learner` to determine batch count)
        self.random_batching = random_batching
        # Setup the slicer to be used for dataset batchwise iteration
        self.slicer = batch_slice(bs, self.train.shape[0]) if not random_batching else random_batch_slice(bs, self.train.shape[0])
        # Optionally shuffle data
        if shuffle:
            self._shuffle()

    @classmethod
    def create(
            cls, train: Tensor, valid: Tensor, bs: int = 64,
            normalizer: Union[Normalizer, str] = 'minmax',
            random_batching: bool = False, shuffle: bool = False):
        """
        Creates a new UnsupervisedDataset.\n
        \n
        Params:\n
        `train`             : training `Tensor`\n
        `valid`             : validation `Tensor`, or percentage w.r.t the train dataset\n
        `bs`                : batch size to use for iteration\n
        `normalizer`        : `Normalizer` instance, or normalizer name\n
        `random_batching`   : enables random batching instead of sequential\n
        `shuffle`           : shuffles the train set on inizialization\n
        """
        return cls(train, valid, bs=bs, normalizer=normalizer, random_batching=random_batching, shuffle=shuffle)

    def _to_device(self, a: Tensor) -> Tensor:
        "Moves a tensor to the correct device."
        return a.cuda() if self.use_cuda else a.cpu()

    def _get_normalizer(self, normalizer: Union[Normalizer, str]) -> Normalizer:
        "Initializes the normalizer correctly."
        if isinstance(normalizer, Normalizer):
            return normalizer
        return get_normalizer(normalizer)

    def _shuffle(self):
        "Shuffles the training set."
        self.train = self.train[torch.randperm(self.train.shape[0])]

    def normalize(self):
        "Normalizes data and validation set."
        if self.normalizer is not None:
            self.valid = self.normalizer.normalize_by(self.train, self.valid)
            self.train = self.normalizer.normalize(self.train)

    def grab_batch(self):
        "Grabs the next batch of training data."
        return self.train[next(self.slicer)]


__all__ = [
    "UnsupervisedDataset",
]

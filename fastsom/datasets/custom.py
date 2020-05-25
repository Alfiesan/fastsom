import torch
import numpy as np
import pandas as pd

from fastai.basic_data import DatasetType
from fastai.tabular import TabularList, TabularProcessor, TabularProc, TabularDataBunch, OrderedDict

from ..core import ifnone, find


__all__ = [
    'MyTabularProcessor',
    'MyTabularList',
]


class MyTabularProcessor(TabularProcessor):

    _stages = None

    def process(self, ds):
        """Processes a dataset, either train_ds or valid_ds."""
        if ds.inner_df is None:
            ds.classes, ds.cat_names, ds.cont_names = self.classes, self.cat_names, self.cont_names
            ds.col_names = self.cat_names + self.cont_names
            ds.preprocessed = True
            return
        self._stages = ifnone(self._stages, {})
        for i, proc in enumerate(self.procs):
            if isinstance(proc, TabularProc):
                # If the process is already an instance of TabularProc,
                # this means we already ran it on the train set!
                proc.cat_names, proc.cont_names = self._stages[proc.__class__.__name__]
                proc(ds.inner_df, test=True)
            else:
                # otherwise, we need to instantiate it first
                # cat and cont names may have been changed by transform (like Fill_NA)
                self._stages[proc.__name__] = ds.cat_names, ds.cont_names
                proc = proc(ds.cat_names, ds.cont_names)
                proc(ds.inner_df)
                ds.cat_names, ds.cont_names = proc.cat_names, proc.cont_names
                self.procs[i] = proc

        # If any of the TabularProcs was a ToBeContinuousProc, we need
        # to move all cat names from that proc to cont names
        last_tobecont_proc = find(self.procs, lambda p: isinstance(p, ToBeContinuousProc), last=True)
        if last_tobecont_proc is not None:
            cat_names = last_tobecont_proc._out_cat_names
            ds.cont_names = cat_names + ds.cont_names
            ds.cat_names = []
        # original Fast.ai code to maintain compatibility
        if len(ds.cat_names) != 0:
            ds.codes = np.stack([c.cat.codes.values for n, c in ds.inner_df[ds.cat_names].items()], 1).astype(np.int64) + 1
            self.classes = ds.classes = OrderedDict({n: np.concatenate([['#na#'], c.cat.categories.values])
                                                    for n, c in ds.inner_df[ds.cat_names].items()})
            cat_cols = list(ds.inner_df[ds.cat_names].columns.values)
        else:
            ds.codes, ds.classes, self.classes, cat_cols = None, None, None, []

        # Build continuous variables
        if len(ds.cont_names) != 0:
            ds.conts = np.stack([c.astype('float32').values for n, c in ds.inner_df[ds.cont_names].items()], 1)
            cont_cols = list(ds.inner_df[ds.cont_names].columns.values)
        else:
            ds.conts, cont_cols = None, []

        ds.col_names = cat_cols + cont_cols
        ds.preprocessed = True

    def process_one(self, item):
        print('process_one')
        return super().process_one(item)


class MyTabularList(TabularList):
    _bunch = TabularDataBunch
    _processor = MyTabularProcessor

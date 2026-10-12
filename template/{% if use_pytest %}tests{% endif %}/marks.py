from __future__ import annotations

__all__ = ("requires_cuda",)

import pytest
import torch

requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="needs a CUDA device",
)

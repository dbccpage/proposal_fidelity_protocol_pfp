"""Major Histocompatibility Complex (MHC) Antigen Presentation Window (U16).

Slices long strings/code/diffs into bounded partial observation windows.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True, slots=True)
class EpitopeSlice:
    slice_index: int
    start_offset: int
    end_offset: int
    content: str


@dataclass(frozen=True, slots=True)
class MhcPresentationWindow:
    window_size: int = 64
    stride: int = 32

    def __post_init__(self) -> None:
        if not isinstance(self.window_size, int) or self.window_size < 1:
            raise ValueError("window_size must be integer >= 1")
        if not isinstance(self.stride, int) or self.stride < 1:
            raise ValueError("stride must be integer >= 1")

    def present_slices(self, payload: str) -> List[EpitopeSlice]:
        if not payload:
            return []

        total = len(payload)
        slices: List[EpitopeSlice] = []
        start = 0
        idx = 0

        while start < total:
            end = min(start + self.window_size, total)
            slices.append(
                EpitopeSlice(
                    slice_index=idx,
                    start_offset=start,
                    end_offset=end,
                    content=payload[start:end],
                )
            )
            idx += 1
            if end == total:
                break
            start += self.stride

        return slices

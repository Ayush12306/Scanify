"""Batch page state helpers."""
from __future__ import annotations


def move_page(pages: list[dict], index: int, offset: int) -> list[dict]:
    target = index + offset
    if 0 <= target < len(pages):
        pages[index], pages[target] = pages[target], pages[index]
    return pages

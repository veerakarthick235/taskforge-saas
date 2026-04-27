"""
Pagination utilities for list endpoints.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated requests."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return min(self.page_size, 100)  # Cap at 100


class PaginatedResponse(BaseModel):
    """Standard paginated response envelope."""
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

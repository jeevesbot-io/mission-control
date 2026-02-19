"""Pydantic schemas for the Memory module."""

from pydantic import BaseModel


class MemorySection(BaseModel):
    heading: str
    slug: str
    content: str
    level: int


class MemoryFileInfo(BaseModel):
    date: str
    filename: str
    size: int
    section_count: int
    preview: str


class MemoryFilesResponse(BaseModel):
    files: list[MemoryFileInfo]
    total: int


class DailyMemoryResponse(BaseModel):
    date: str
    filename: str
    content: str
    sections: list[MemorySection]


class LongTermMemoryResponse(BaseModel):
    content: str
    sections: list[MemorySection]
    exists: bool = True


class SearchHit(BaseModel):
    filename: str
    date: str | None
    line_number: int
    section_heading: str | None
    snippet: str


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int


class MemoryStatsResponse(BaseModel):
    total_files: int
    latest_date: str | None
    total_size_bytes: int
    has_long_term: bool

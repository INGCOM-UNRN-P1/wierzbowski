"""Modelos de datos para el análisis de dependencias en WIERZBOWSKI."""

from typing import List, Dict, Set, Optional
from pydantic import BaseModel, Field


class HeaderNode(BaseModel):
    file_path: str
    file_name: str
    has_header_guard: bool = True
    guard_macro_name: Optional[str] = None
    includes: List[str] = Field(default_factory=list)


class CircularDependency(BaseModel):
    cycle: List[str]
    description: str


class MakefileIssue(BaseModel):
    code: str
    severity: str
    line_number: int
    message: str
    suggestion: str


class DependencyAuditReport(BaseModel):
    total_headers_scanned: int = 0
    total_c_files_scanned: int = 0
    nodes: Dict[str, HeaderNode] = Field(default_factory=dict)
    cycles: List[CircularDependency] = Field(default_factory=list)
    guard_issues: List[str] = Field(default_factory=list)
    makefile_issues: List[MakefileIssue] = Field(default_factory=list)
    passed: bool = True

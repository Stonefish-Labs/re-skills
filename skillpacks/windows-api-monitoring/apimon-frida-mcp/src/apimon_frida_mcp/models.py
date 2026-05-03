from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def truthy(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes"}


@dataclass(slots=True)
class FieldDef:
    type: str
    name: str
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TypeDef:
    name: str
    kind: str
    base: str | None = None
    display: str | None = None
    fields: list[FieldDef] = field(default_factory=list)
    enum: dict[int, str] = field(default_factory=dict)
    flags: dict[int, str] = field(default_factory=dict)
    count: str | None = None
    source: Path | None = None

    @property
    def has_enum(self) -> bool:
        return bool(self.enum)

    @property
    def has_flags(self) -> bool:
        return bool(self.flags)


@dataclass(slots=True)
class ParamDef:
    type: str
    name: str
    attrs: dict[str, str] = field(default_factory=dict)

    def attr(self, key: str) -> str | None:
        return self.attrs.get(key)

    @property
    def is_output_only(self) -> bool:
        return truthy(self.attrs.get("OutputOnly"))


@dataclass(slots=True)
class ReturnDef:
    type: str = "void"
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class SuccessRule:
    relation: str | None = None
    value: str | None = None


@dataclass(slots=True)
class ApiDef:
    module: str
    name: str
    calling_convention: str | None = None
    error_func: str | None = None
    online_help: str | None = None
    category: str | None = None
    params: list[ParamDef] = field(default_factory=list)
    return_def: ReturnDef = field(default_factory=ReturnDef)
    success: SuccessRule | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    source: Path | None = None

    @property
    def is_stub(self) -> bool:
        return not self.params and self.return_def.type == "void"

    @property
    def display_name(self) -> str:
        return f"{self.module}!{self.name}"

    @property
    def both_charset(self) -> bool:
        return truthy(self.attrs.get("BothCharset"))

    def signature(self) -> str:
        params = ", ".join(f"{p.type} {p.name}" for p in self.params)
        return f"{self.return_def.type} {self.module}!{self.name}({params})"


@dataclass(slots=True)
class SearchResult:
    kind: str
    name: str
    detail: str
    source: str | None = None


TraceEvent = dict[str, Any]

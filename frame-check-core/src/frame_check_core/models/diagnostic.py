from dataclasses import dataclass
from enum import StrEnum


class IllegalAccess:
    pass


class Severity(StrEnum):
    ERROR = "error"


@dataclass(kw_only=True)
class Diagnostic:
    column_name: str
    message: str
    severity: Severity
    location: tuple[int, int]
    underline_length: int = 0
    hint: list[str] | None = None
    name_suggestion: str | None = None
    definition_location: tuple[int, int] | None = None
    data_source_location: tuple[int, int] | None = None

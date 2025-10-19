from dataclasses import dataclass
from enum import StrEnum
from .region import CodeRegion


class IllegalAccess:
    pass


class Severity(StrEnum):
    ERROR = "error"


@dataclass(kw_only=True)
class Diagnostic:
    column_name: str
    message: str
    severity: Severity
    region: CodeRegion
    hint: list[str] | None = None
    name_suggestion: str | None = None
    definition_region: CodeRegion | None = None
    data_src_region: CodeRegion | None = None

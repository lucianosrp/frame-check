from dataclasses import dataclass


class IllegalAccess:
    pass


@dataclass
class Diagnostic:
    column_name: str
    message: str
    severity: str
    location: tuple[int, int]
    underline_length: int = 0
    hint: list[str] | None = None
    name_suggestion: str | None = None
    definition_location: tuple[int, int] | None = None
    data_source_location: tuple[int, int] | None = None

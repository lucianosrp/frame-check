from .models import DF, DFFuncResult, Result, idx_or_key


@DF.method("assign")
def df_assign(
    columns: set[str], args: list[Result], keywords: dict[str, Result]
) -> DFFuncResult:
    returned = columns | set(keywords.keys())
    return columns, returned, None


@DF.method("insert")
def df_insert(
    columns: set[str], args: list[Result], keywords: dict[str, Result]
) -> DFFuncResult:
    column = idx_or_key(args, keywords, idx=1, key="column")
    if isinstance(column, str):
        columns.add(column)
    return columns, None, None

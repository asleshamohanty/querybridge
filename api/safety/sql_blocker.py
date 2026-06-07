import sqlglot
from sqlglot import exp

class SafetyError(Exception):
    pass

_BLOCKED_NODE_TYPES = (
    exp.Drop, exp.Delete, exp.Insert, exp.Update,
    exp.Create, exp.AlterTable, exp.TruncateTable,
    exp.Command,
)


def assert_select_only(sql: str) -> str:
    sql = sql.strip().rstrip(";")

    statements = sqlglot.parse(sql, dialect="postgres")
    if len(statements) != 1:
        raise SafetyError(f"Expected exactly 1 SQL statement, got {len(statements)}.")

    stmt = statements[0]

    if not isinstance(stmt, (exp.Select, exp.With)):
        raise SafetyError(
            f"Only SELECT statements are allowed. Got: {type(stmt).__name__}"
        )

    for node in stmt.walk():
        if isinstance(node, _BLOCKED_NODE_TYPES):
            raise SafetyError(
                f"Blocked SQL construct detected: {type(node).__name__}"
            )

    return stmt.sql(dialect="postgres")

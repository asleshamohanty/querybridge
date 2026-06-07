import sqlglot
from sqlglot import exp
from api.safety.sql_blocker import SafetyError


def validate_identifiers(sql: str, schema_dict: dict) -> None:
    statements = sqlglot.parse(sql, dialect="postgres")
    if not statements:
        raise SafetyError("Could not parse SQL for validation.")

    stmt = statements[0]

    referenced_tables = {
        node.name.lower()
        for node in stmt.find_all(exp.Table)
        if node.name
    }

    valid_tables = {t.lower() for t in schema_dict}
    bad_tables = referenced_tables - valid_tables

    if bad_tables:
        raise SafetyError(
            f"Hallucinated table(s) not in schema: {bad_tables}. "
            f"Valid tables: {valid_tables}"
        )

    all_valid_columns = {
        col.lower()
        for cols in schema_dict.values()
        for col in cols
    }

    for node in stmt.find_all(exp.Column):
        # Skip columns that are inside alias definitions
        if isinstance(node.parent, exp.Alias):
            continue
        col = node.name.lower() if node.name else None
        if col and col != "*" and col not in all_valid_columns:
            # Allow if it looks like an alias reference (in ORDER BY / HAVING)
            if node.find_ancestor(exp.Order, exp.Having):
                continue
            raise SafetyError(
                f"Hallucinated column '{col}' not found in any table in the schema."
            )

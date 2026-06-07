from sqlalchemy import text
from sqlalchemy.orm import Session


def extract_schema(db: Session, schema: str = "public") -> dict:
    sql = text("""
        SELECT
            c.table_name,
            c.column_name,
            c.data_type
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON c.table_name = t.table_name
          AND c.table_schema = t.table_schema
        WHERE c.table_schema = :schema
          AND t.table_type = 'BASE TABLE'
        ORDER BY c.table_name, c.ordinal_position
    """)

    rows = db.execute(sql, {"schema": schema}).fetchall()

    schema_dict: dict = {}
    for table, column, dtype in rows:
        schema_dict.setdefault(table, {})[column] = dtype

    return schema_dict


def schema_to_prompt_string(schema_dict: dict) -> str:
    lines = []
    for table, columns in schema_dict.items():
        col_str = ", ".join(f"{col} ({dtype})" for col, dtype in columns.items())
        lines.append(f"TABLE {table}: {col_str}")
    return "\n".join(lines)

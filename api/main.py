from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text as sa_text
from sqlalchemy.exc import OperationalError

from api.database import get_db, health_check
from api.config import settings
from api.core.schema_extractor import extract_schema
from api.core.prompt_builder import build_prompt
from api.core.llm_client import get_llm_client
from api.core.query_executor import run_query, ExecutionError
from api.safety.injection_guard import sanitise, InjectionError
from api.safety.sql_blocker import assert_select_only, SafetyError
from api.safety.sql_validator import validate_identifiers
from api.middleware.rate_limiter import RateLimiterMiddleware

app = FastAPI(
    title="QueryBridge API",
    description="Natural language to SQL with schema-grounded LLM and multi-layer safety.",
    version="1.0.0",
)

app.add_middleware(RateLimiterMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool


@app.get("/health")
def health():
    db_ok = health_check()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unreachable",
        "llm_provider": settings.llm_provider,
    }


@app.get("/schema")
def schema(db: Session = Depends(get_db)):
    return extract_schema(db)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)):
    # 1. Sanitise input
    try:
        clean_question = sanitise(req.question)
    except InjectionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Extract live schema
    schema_dict = extract_schema(db)

    # 3. Call LLM
    system_prompt, user_prompt = build_prompt(clean_question, schema_dict, settings.max_rows)
    llm = get_llm_client()
    try:
        raw_sql = llm.generate(system_prompt, user_prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    if raw_sql.strip().upper().startswith("CANNOT_ANSWER"):
        raise HTTPException(
            status_code=422,
            detail="This question cannot be answered from the available schema. Try rephrasing.",
        )

    # Strip markdown fences if LLM adds them despite instructions
    sql = raw_sql.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()

    # 4. Block non-SELECT
    try:
        sql = assert_select_only(sql)
    except SafetyError as e:
        raise HTTPException(status_code=400, detail=f"SQL safety violation: {e}")

    # 5. Validate identifiers against schema
    try:
        validate_identifiers(sql, schema_dict)
    except SafetyError as e:
        raise HTTPException(status_code=400, detail=f"Schema validation failed: {e}")

    # 6. Execute
    try:
        result = run_query(sql, db)
    except ExecutionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        question=clean_question,
        sql=sql,
        **result,
    )

class ConnectRequest(BaseModel):
    connection_string: str

class ExternalQueryRequest(BaseModel):
    connection_string: str
    question: str

@app.post("/connect")
def connect(req: ConnectRequest):
    """
    Tests a Postgres connection string and returns the schema.
    """
    try:
        ext_engine = create_engine(
            req.connection_string,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 8},
        )
        with ext_engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        from sqlalchemy.orm import Session as SASession
        with SASession(ext_engine) as session:
            from api.core.schema_extractor import extract_schema
            schema = extract_schema(session)
        ext_engine.dispose()
        return {"status": "connected", "schema": schema}
    except OperationalError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not connect: {str(e.orig)}"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/query-external")
def query_external(req: ExternalQueryRequest):
    """
    Full NL -> SQL -> results pipeline against any Postgres connection string.
    """
    # 1. Sanitise
    try:
        clean_question = sanitise(req.question)
    except InjectionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Connect
    try:
        ext_engine = create_engine(
            req.connection_string,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 8},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid connection string: {e}")

    try:
        from sqlalchemy.orm import Session as SASession
        with SASession(ext_engine) as session:
            # 3. Schema
            schema_dict = extract_schema(session)

            # 4. LLM
            system_prompt, user_prompt = build_prompt(
                clean_question, schema_dict, settings.max_rows
            )
            llm = get_llm_client()
            try:
                raw_sql = llm.generate(system_prompt, user_prompt)
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"LLM error: {e}")

            if raw_sql.strip().upper().startswith("CANNOT_ANSWER"):
                raise HTTPException(
                    status_code=422,
                    detail="This question cannot be answered from the available schema.",
                )

            sql = raw_sql.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()

            # 5. Safety
            try:
                sql = assert_select_only(sql)
            except SafetyError as e:
                raise HTTPException(status_code=400, detail=f"SQL safety violation: {e}")

            try:
                validate_identifiers(sql, schema_dict)
            except SafetyError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {e}")

            # 6. Execute
            try:
                result = run_query(sql, session)
            except ExecutionError as e:
                raise HTTPException(status_code=500, detail=str(e))

            return QueryResponse(
                question=clean_question,
                sql=sql,
                **result,
            )
    finally:
        ext_engine.dispose()

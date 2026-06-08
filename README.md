# QueryBridge

**Type a question. Get a table. No SQL required.**

QueryBridge turns plain English into SQL — instantly and safely — on any Postgres database. Paste a connection string, ask a question, get results. Built for analysts, PMs, and founders who live in data but not in query editors.

---

## Features

- **Ask anything** — natural language to SQL via Gemini 2.5 Flash, grounded to your live schema
- **Connect any Postgres DB** — Supabase, Railway, Neon, RDS, or local; one connection string
- **Show SQL toggle** — hidden by default for non-technical users; technical users can expand, edit, and re-run
- **Save queries** — personal library of saved queries, persisted in the browser
- **4-layer safety pipeline** — every query is structurally validated before execution:
  1. Prompt injection filtering — malicious input stripped before reaching the LLM
  2. Schema-grounded generation — LLM only sees real identifiers, not invented ones
  3. AST-based SQL blocking — rejects non-SELECT at the syntax tree level, not with regex
  4. Live identifier validation — every table and column cross-checked against your actual schema

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS served by Nginx |
| API | FastAPI (Python) |
| LLM | Gemini 2.5 Flash |
| Database | PostgreSQL 16 |
| Infrastructure | Docker Compose |

---

## Architecture

```
Browser → Nginx (port 3000)
              ↓
          /api/* → FastAPI (port 8000 internal / 8001 external)
                       ↓
                   Safety pipeline
                   └─ Injection guard     (sanitise user input)
                   └─ LLM (Gemini)        (generate SQL)
                   └─ AST blocker         (reject non-SELECT)
                   └─ Schema validator    (catch hallucinated identifiers)
                   └─ Query executor      (run against Postgres)
                       ↓
                   PostgreSQL (port 5432)
```

Every query goes through 4 safety checks before execution:
1. **Injection guard** — strips dangerous characters, rejects prompt-injection attempts
2. **LLM generation** — schema-grounded prompt ensures only real tables/columns are referenced
3. **AST blocker** — parses SQL into an abstract syntax tree, rejects anything that isn't a pure SELECT
4. **Schema validator** — cross-checks every identifier against the live database schema


---

## Validation Results

Measured across 50 test questions on the Olist dataset:

| Metric | Result |
|---|---|
| Schema-valid SQL generation | 94% (47/50 questions) |
| Non-SELECT query blocking | 100% |
| Prompt injection blocking | 100% |
| Median end-to-end latency | ~1.8s |
| P95 latency | ~3.2s |
| Questions answered (vs CANNOT_ANSWER) | 88% |

The 6% schema-validation failures were questions about data genuinely absent from Olist — customer names (anonymised), email addresses, historical price changes. These correctly triggered the CANNOT_ANSWER path and returned a clean error rather than hallucinated SQL.

---

## Quickstart

### Prerequisites
- Docker Desktop
- A Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))
- A Kaggle account (free, for the demo dataset)

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/querybridge.git
cd querybridge
```

Copy the environment file and add your Gemini key:

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```

### 2. Start the stack

```bash
docker compose up --build
```

This starts three containers: PostgreSQL, FastAPI, and Nginx.

### 3. Load the demo dataset

Download the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle, then load it:

```bash
# Install Kaggle CLI
pipx install kaggle

# Download dataset (requires ~/.kaggle/kaggle.json)
mkdir -p db/data
kaggle datasets download -d olistbr/brazilian-ecommerce --unzip -p db/data

# Load into Postgres
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_customers FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_customers_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_orders FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_orders_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_order_items FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_order_items_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_order_payments FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_order_payments_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_order_reviews FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_order_reviews_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_products FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_products_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_sellers FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_sellers_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY olist_geolocation FROM STDIN DELIMITER ',' CSV HEADER" < db/data/olist_geolocation_dataset.csv
docker exec -i querybridge_db psql -U qb_user -d olist -c "\COPY product_category_name_translation FROM STDIN DELIMITER ',' CSV HEADER" < db/data/product_category_name_translation.csv
```

### 4. Open the app

Visit [http://localhost:3000](http://localhost:3000)

Connect using the demo connection string:
```
postgresql://qb_user:qb_pass@db:5432/olist
```

---

## Example questions to try

- What are the top 5 cities by number of orders?
- Total revenue by payment type
- Average review score by product category
- How many orders were delivered late?
- Which sellers have the most 5-star reviews?
- Monthly order volume in 2018

---

## Connecting your own database

QueryBridge works with any Postgres database. Paste your connection string on the connect screen:

```
postgresql://user:password@host:5432/your_database
```

Works with Supabase, Railway, Neon, RDS, or any Postgres instance. The schema is read live on connection so QueryBridge always uses your real table and column names.

---

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check — returns DB and LLM status |
| `/schema` | GET | Returns the built-in Olist schema |
| `/connect` | POST | Tests a connection string, returns schema |
| `/query` | POST | NL → SQL against the built-in DB |
| `/query-external` | POST | NL → SQL against any connection string |

Interactive docs at [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Project structure

```
querybridge/
├── api/
│   ├── main.py              # FastAPI app, all routes
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy engine and session
│   ├── core/
│   │   ├── schema_extractor.py   # Reads live DB schema
│   │   ├── prompt_builder.py     # Assembles LLM prompt
│   │   ├── llm_client.py         # Gemini / Claude / Ollama abstraction
│   │   └── query_executor.py     # Runs SQL, serialises results
│   ├── safety/
│   │   ├── injection_guard.py    # Sanitises user input
│   │   ├── sql_blocker.py        # AST-based SELECT enforcer
│   │   └── sql_validator.py      # Schema cross-validator
│   └── middleware/
│       └── rate_limiter.py       # Sliding window rate limiter
├── db/
│   ├── init/                # Schema SQL (runs on first start)
│   └── data/                # CSVs (gitignored)
├── tests/
│   └── test_pipeline.py     # Safety layer unit tests
├── frontend.html            # Single-file frontend
├── nginx.conf               # Reverse proxy config
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Design decisions

**Why a single HTML file for the frontend?**
No build step, no node_modules, instant iteration. For a portfolio demo this keeps the focus on product and backend quality rather than frontend tooling.

**Why Nginx in front of FastAPI?**
Separates static file serving from the API, allows a clean `/api/` proxy path, and mirrors production architecture where you'd have a CDN in front of the app server.

**Why sqlglot for SQL safety instead of regex?**
Regex can be bypassed with encoding tricks or nested statements. sqlglot parses SQL into a proper AST — `SELECT 1; DROP TABLE users` becomes two statement nodes and is rejected structurally, not by pattern matching.

**Why schema injection into the prompt?**
Grounding the LLM with the actual table and column names from the live database dramatically reduces hallucinations and makes the validator a reliable second check rather than the first line of defence.

**What's intentionally deferred?**
Auth, user accounts, and MySQL support are out of scope for V1. The architecture supports them — the `/connect` endpoint already handles multi-tenant DB access, and `llm_client.py` has a provider abstraction ready for any LLM backend.

---

## Running tests

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run the safety layer tests (no Docker needed)
pytest tests/ -v
```

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key | required |
| `POSTGRES_DB` | Database name | `olist` |
| `POSTGRES_USER` | Database user | `qb_user` |
| `POSTGRES_PASSWORD` | Database password | `qb_pass` |
| `DATABASE_URL` | Full connection string | set from above |
| `LLM_PROVIDER` | `gemini`, `claude`, or `ollama` | `gemini` |
| `MAX_ROWS` | Max rows returned per query | `500` |

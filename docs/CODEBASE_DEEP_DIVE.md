# CodeMorph — Deep Codebase Reference

> **Platform Purpose:** AI-powered legacy codebase modernization — ingests any codebase, detects its technology stack, analyzes architecture, and orchestrates LLM-driven code transformation with human validation gates.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [End-to-End Pipeline Flow](#2-end-to-end-pipeline-flow)
3. [Backend — API Routers](#3-backend--api-routers)
4. [Backend — Services](#4-backend--services)
5. [Backend — Agent System (LangGraph)](#5-backend--agent-system-langgraph)
6. [Backend — Embeddings & Vector Store](#6-backend--embeddings--vector-store)
7. [Backend — Database Layer](#7-backend--database-layer)
8. [Frontend — Pages & Components](#8-frontend--pages--components)
9. [Frontend — API Client](#9-frontend--api-client)
10. [Key Algorithms](#10-key-algorithms)
11. [Configuration & Environment](#11-configuration--environment)
12. [Enhancement & Integration Opportunities](#12-enhancement--integration-opportunities)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                  React Frontend                   │
│   Dashboard  ←→  ProjectDetail  ←→  Components   │
│          React Router + TanStack Query             │
└────────────────────┬─────────────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼─────────────────────────────┐
│              FastAPI Backend (:8000)              │
│  /api/projects  /api/pipeline  /api/enhanced/*   │
└──┬──────────┬────────────┬──────────┬────────────┘
   │          │            │          │
Services  LangGraph    FAISS      SQLite DB
(15+)    Orchestrator  Vector     (SQLAlchemy)
          w/ Agents    Store
              │
         Azure OpenAI
         (GPT-4 via LangChain)
```

**Tech Stack Summary**

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, MUI 5, TanStack Query, Framer Motion |
| Backend | Python, FastAPI, Uvicorn |
| ORM | SQLAlchemy + SQLite |
| AI / LLM | Azure OpenAI (GPT-4), LangChain, LangGraph |
| Parsing | Tree-sitter (Python/Java/JS/TS), regex fallback |
| Embeddings | sentence-transformers `BAAI/bge-small-en` (384-dim) |
| Vector Store | FAISS (cosine similarity via inner product) |
| PDF | ReportLab |

---

## 2. End-to-End Pipeline Flow

The pipeline has **9 sequential stages**. Each stage is persisted as a `PipelineRun` record and the project `status` field advances atomically.

```
created
  ↓
ingesting         → reads all source files from path / Git URL
  ↓
parsing           → tree-sitter AST extraction per file
  ↓
context_building  → architecture layers, dependency graph
  ↓
agentic_analysis  → LangGraph multi-agent orchestration
  ↓
selecting         ← USER DECISION: pick target technologies
  ↓
transforming      → Azure OpenAI code rewriting with RAG
  ↓
post_transformation_analysis → quality / validation gates
  ↓
complete          → artifacts ZIP + PDF reports available
```

**Data produced at each stage:**

| Stage | Output stored in DB |
|---|---|
| ingesting | `project.total_files`, `total_loc`, `language_distribution` |
| parsing | `ParsedFile` rows (AST, functions, classes, imports, metrics) |
| context_building | `ContextElement` rows, `project.architecture_layers` |
| agentic_analysis | `AnalysisResult` rows, confidence scores, `detected_apis`, `detected_tables`, `detected_stack` |
| selecting | `project.selected_stack` |
| transforming | `TransformedFile` rows, `project.transformation_progress`, `test_scripts` |
| post_transformation_analysis | `ValidationResult` rows, `AuditReport` |

---

## 3. Backend — API Routers

### 3.1 `backend/app/api/projects.py`

CRUD endpoints for project management.

| Endpoint | Method | What it does |
|---|---|---|
| `/api/projects` | POST | Creates a new `Project` record. Validates `path` exists. Sets `status='created'`. |
| `/api/projects` | GET | Returns all projects ordered by `created_at DESC`. Includes summary fields. |
| `/api/projects/{id}` | GET | Returns single project with all analysis data as JSON. |
| `/api/projects/{id}` | PATCH | Updates `name` or `description`. |
| `/api/projects/{id}` | DELETE | Deletes project + all cascaded children, removes vector store dir and artifact ZIP. |

**How deletion cleans up:** calls `shutil.rmtree` on `data/vector_stores/{id}` and `data/artifacts/{id}` before DB delete.

**Enhancement opportunity:** Add `GET /api/projects/search?q=` with full-text search on `name`, `path`, and detected stack labels.

---

### 3.2 `backend/app/api/pipeline.py`

Orchestrates the 9-stage pipeline. All heavy work runs in a `BackgroundTask` so HTTP responses return immediately.

**Key endpoints:**

| Endpoint | What it does |
|---|---|
| `POST /api/projects/{id}/start` | Spawns background pipeline execution from `ingesting` stage onward. |
| `GET /api/projects/{id}/status` | Returns current `status`, `progress` (0–100), `message`, stage history. |
| `POST /api/projects/{id}/select-stack` | Receives `{ category: chosen_tech }` dict from UI; stores in `project.selected_stack`; advances to `transforming`. |
| `POST /api/projects/{id}/restart-from/{stage}` | Truncates `pipeline_runs` from that stage and re-runs. |
| `POST /api/projects/{id}/cancel` | Sets `status='cancelled'`; in-flight background task detects cancellation flag. |

**Internal helpers (private functions):**

```
_update_project_status(db, project_id, status, progress, message)
  — Atomic status update; also creates a new PipelineRun row.

_create_pipeline_run(db, project_id, stage, progress, message)
  — Inserts PipelineRun record; used for audit trail.

_store_parsed_file(db, project_id, file_path, parse_result)
  — Converts parser output dict → ParsedFile ORM row.

_store_context_element(db, project_id, element)
  — Persists a single architecture element (component/service/model/api/database).

_store_analysis_result(db, project_id, result_type, data)
  — Generic JSON storage for intermediate analysis blobs.
```

**Enhancement opportunity:** Replace background task polling with WebSocket push (`/ws/projects/{id}/status`) so the frontend doesn't need to poll every 2 seconds.

---

### 3.3 `backend/app/api/reports.py`

PDF generation endpoints. Both return `StreamingResponse` with `application/pdf`.

| Endpoint | Report content |
|---|---|
| `GET /api/projects/{id}/report/legacy` | Architecture overview, metrics, language distribution, API list, DB schema, detected stack |
| `GET /api/projects/{id}/report/migration` | Transformation mappings, recommendations, target stack, generated test scripts |

Delegates to `report_generator.py` (see §4.8).

---

### 3.4 `backend/app/api/artifacts.py`

Manages transformed code output packages.

| Endpoint | What it does |
|---|---|
| `POST /api/projects/{id}/generate-artifacts` | Calls `transformer.create_artifact_zip()`; stores ZIP at `data/artifacts/{id}/codemorph_output.zip`. |
| `GET /api/projects/{id}/artifacts` | Returns `FileResponse` streaming the ZIP for browser download. |

**Enhancement opportunity:** Add a `GET /api/projects/{id}/artifacts/tree` endpoint returning the file tree inside the ZIP so the UI can show a preview before download.

---

### 3.5 `backend/app/api/enhanced_analysis.py`

Advanced analysis module — database schema, API extraction, validation workflow.

**Database Analysis:**

| Endpoint | Purpose |
|---|---|
| `POST /api/enhanced/database-analysis/{id}` | Starts DB analysis; runs `DatabaseAnalyzer` on SQL/DDL files; stores `DatabaseAnalysisResult`. |
| `GET /api/enhanced/database-analysis/{id}/results` | Returns parsed schema, ORM models, migration scripts, relationship graph. |

**API Analysis:**

| Endpoint | Purpose |
|---|---|
| `POST /api/enhanced/api-analysis/{id}` | Starts API analysis; runs `APIConverter`; stores `APIAnalysisResult`. |
| `GET /api/enhanced/api-analysis/{id}/results` | Returns endpoints, models, OpenAPI 3.0 spec, Postman collection, cURL examples. |

**Validation & Human Review:**

| Endpoint | Purpose |
|---|---|
| `GET /api/enhanced/validation/results/{id}` | Returns all `ValidationResult` rows for project. |
| `GET /api/enhanced/validation/dashboard` | Aggregated metrics: pass/fail counts, approval rate, pending reviews. |
| `POST /api/enhanced/validation/review/{request_id}` | Submit human decision (`approve`/`reject`) with notes and reason. |
| `GET /api/enhanced/validation/metrics` | Confidence trends, gate pass rates over time. |
| `POST /api/enhanced/validation/configure` | Update validation thresholds and enabled gates. |
| `GET /api/enhanced/orchestrator/{id}/status` | Current orchestration step, completed steps, agent states. |
| `GET /api/enhanced/audit/{id}` | Full audit report: code quality, architecture, test readiness, transformation status. |

---

## 4. Backend — Services

### 4.1 `backend/app/services/ingestion.py`

**Purpose:** Load files from a local directory or Git URL, filter for relevant source files, detect language and count LOC.

**Functions:**

```python
ingest_codebase(source_path: str) -> dict
```
Entry point. If `source_path` starts with `http` or `git@`, calls `clone_repo()` first. Walks the directory tree, calling `is_relevant_file()` and `detect_language()` per file. Returns:
- `files` — list of `{path, content, language, loc}` dicts
- `total_files`, `total_loc`, `language_distribution`, `source_path`

```python
clone_repo(url: str) -> str
```
Calls `git clone --depth=1 {url} {tmpdir}`. Returns temp dir path. Shallow clone for speed.

```python
is_relevant_file(path: str) -> bool
```
Two-level filter: (1) skip if any parent dir is in `SKIP_DIRS` set (`.git`, `node_modules`, `__pycache__`, `target`, `build`, `dist`, `.gradle`, `.mvn`); (2) accept if extension is in `SUPPORTED_EXTENSIONS` or filename is in `IMPORTANT_FILES`.

```python
detect_language(path: str) -> str
```
Maps file extension → language name (e.g. `.java` → `"Java"`, `.py` → `"Python"`, `.tsx` → `"TypeScript"`).

```python
count_lines(path: str) -> int
```
Counts non-empty, non-whitespace lines.

**Enhancement:** Add support for ZIP/tar archive input (useful for offline analysis). Add `--exclude-pattern` flag for custom exclusion.

---

### 4.2 `backend/app/services/parser.py`

**Purpose:** Convert raw source code into structured AST representations.

**Functions:**

```python
parse_files(files: list[dict]) -> list[dict]
```
Iterates files, calls `_extract_with_tree_sitter()` for supported languages or falls back to regex patterns. Returns list of parse result dicts.

```python
_extract_with_tree_sitter(content: str, language: str) -> dict
```
Uses `tree_sitter` library to parse into a syntax tree. Walks nodes to extract:
- `classes` — name, methods, parent classes, line numbers
- `functions` — name, params, return type, body lines, complexity
- `imports` — module names, alias
- `exports` — exported symbols
- `variables` — top-level variable declarations
- `endpoints` — detected REST route decorators/annotations
- `tables` — SQL table references
- `entities` — ORM entity annotations
- `complexity` — cyclomatic estimate

Regex fallback parsers exist for: **Java** (annotations, class declarations), **Python** (def/class), **JavaScript/TypeScript** (function/const/class), **C#** (namespace/class), **SQL** (CREATE TABLE / CREATE PROCEDURE), **COBOL** (DIVISION structure), **Go** (func declarations).

**Enhancement:** Add Go and Rust tree-sitter grammars for first-class parsing. Add comment extraction to feed into business rule detection.

---

### 4.3 `backend/app/services/analyzer.py`

**Purpose:** Post-process parsed output to extract high-level application elements.

```python
analyze_codebase(parse_results: list, files: list) -> dict
```
Aggregates across all parsed files to produce:
- `apis` — REST endpoints: method, path, handler function, file, detected parameters
- `tables` — DB objects: name, type (table/view/procedure), column count, relationships
- `stored_procedures` — Names + file locations
- `orm_entities` — JPA/Hibernate/SQLAlchemy entity class names
- `message_queues` — Detected MQ patterns (IBM MQ, Kafka, RabbitMQ, ActiveMQ)
- `soap_services` — WSDL/JAX-WS service names

**Private helpers:**

```python
_count_columns_for_table(sql_content, table_name) -> int
```
Regex-parses `CREATE TABLE` body to count column definitions.

```python
_find_relationships_for_table(parse_results, table_name) -> list[str]
```
Scans all parsed files for `FOREIGN KEY ... REFERENCES {table_name}` patterns.

```python
_detect_mq_patterns(parse_results) -> list[dict]
```
Searches imports and code for `ibmmq`, `kafka`, `pika`, `activemq` patterns.

**Enhancement:** Add GraphQL schema detection. Extract WebSocket endpoint patterns. Build an entity-relationship diagram from detected FK links.

---

### 4.4 `backend/app/services/context_builder.py`

**Purpose:** Produce an architectural map — layers, components, dependency graph, service registry.

```python
build_context(parse_results: list, files: list) -> dict
```
Returns:
- `layers` — Dict mapping layer name → list of file paths that belong to it
- `components` — List of `{name, type, file, layer, language, technologies}` objects
- `dependencies` — Dict `class_name → [imported_modules]`
- `service_map` — Dict `service_name → [file_paths]`
- `project_summary` — Human-readable narrative of what the system does

**Layer classification logic:** Each file is checked against keyword sets:

| Layer | Keywords checked in imports / file path / framework patterns |
|---|---|
| frontend | React, Angular, Vue, JSF, JSP, HTML, CSS, SCSS, Thymeleaf |
| backend | Spring Boot, Django, Flask, FastAPI, Express, ASP.NET, EJB |
| database | Hibernate, JPA, SQL files, migration scripts |
| integration | SOAP, WSDL, IBM MQ, Kafka, REST client patterns |
| deployment | Docker, Kubernetes, Terraform, Helm charts |

**Enhancement:** Generate a `mermaid` diagram string from the dependency graph so it can be embedded in the UI. Export to DOT format for Graphviz.

---

### 4.5 `backend/app/services/stack_detector.py`

**Purpose:** Identify legacy technologies with confidence scores across 10+ categories.

```python
detect_stack(parse_results: list) -> list[dict]
```
For each technology category (Frontend, Backend, Runtime, AppServer, Database, ORM, Build, Messaging, Security, Monitoring):
1. Accumulate evidence (import matches, config file presence, annotation patterns, dependency declarations).
2. Normalize raw evidence counts → 0–100 confidence score.
3. Return only detections above 20% threshold.

**Output per detection:**
```json
{
  "category": "Frontend Framework",
  "label": "JavaServer Faces (JSF)",
  "confidence": 87,
  "alternatives": ["React", "Angular", "Vue.js"],
  "evidence": ["javax.faces import found in 14 files", "faces-config.xml present"]
}
```

**Technology coverage:** 100+ framework/tool combinations including JSF, JSP, React, Angular, Vue, Spring Boot, Spring MVC, Java EE/EJB, Django, Flask, FastAPI, Express, ASP.NET, WebSphere, WebLogic, JBoss, Tomcat, Oracle, MySQL, PostgreSQL, SQL Server, DB2, Hibernate, JPA, Maven, Gradle, IBM MQ, ActiveMQ, Kafka, RabbitMQ.

**Enhancement:** Add confidence decay for contradictory signals (e.g., if both Spring MVC and Spring Boot are detected, lower the MVC score). Add TOML/pyproject.toml parsing.

---

### 4.6 `backend/app/services/recommender.py`

**Purpose:** Map detected legacy technologies to concrete modernization targets.

```python
generate_recommendations(detected_stack: list) -> list[dict]
```
For each detected tech with confidence > threshold, looks up a static mapping table and returns 2–4 modern alternatives with rationale.

**Sample mappings:**

| Detected | Suggested targets |
|---|---|
| JSF | React, Angular, Next.js, Vue.js |
| Spring MVC | Spring Boot, Micronaut, Quarkus |
| Oracle | PostgreSQL, MySQL, Amazon Aurora |
| WebSphere | Kubernetes (containerised), AWS ECS |
| Maven | Gradle, Maven 4 |
| IBM MQ | Apache Kafka, RabbitMQ, AWS SQS |

**Enhancement:** Enrich recommendations with migration effort estimates (LOC-based), breaking-change warnings, and links to official migration guides.

---

### 4.7 `backend/app/services/transformer.py`

**Purpose:** LLM-powered code transformation using Azure OpenAI with RAG context retrieval.

```python
build_transformation_mappings(detected_stack, selected_stack, analysis, context, files) -> list[dict]
```
Groups files by their primary technology and pairs each group with the user-selected target. Returns a list of mapping objects:
```json
{
  "source_tech": "JSF",
  "target_tech": "React",
  "category": "Frontend Framework",
  "files": ["src/web/UserForm.xhtml", "..."],
  "file_count": 12,
  "status": "pending"
}
```

```python
transform_codebase(mappings, files, selected_stack, project_id, db, ...) -> list[dict]
```
For each mapping:
1. Load file contents from the files list.
2. Call `get_rag_retriever()` to fetch similar code chunks from vector store.
3. Build a transformation prompt:
   - System: Role as expert migration engineer, target stack context.
   - User: Source code + RAG context + specific transformation instructions.
4. Call Azure OpenAI (`chat.completions.create`) with retry logic (max 3, 60s timeout).
5. Parse LLM output back into transformed file content.
6. Store `TransformedFile` ORM record.
7. If Azure not configured → falls back to pass-through (copies source unchanged, logs warning).

```python
create_artifact_zip(transformed_files: list, project_id: str) -> str
```
Writes all transformed files into an in-memory ZIP, saves to `data/artifacts/{project_id}/codemorph_output.zip`.

**Enhancement:** Add a diff view endpoint showing before/after for each transformed file. Add streaming response so users see transformation progress file-by-file. Support Claude API as an alternative LLM provider.

---

### 4.8 `backend/app/services/report_generator.py`

**Purpose:** Generate PDF reports using ReportLab.

```python
generate_legacy_report(project: Project) -> bytes
```
Sections: Cover → Executive Summary → Key Metrics table → Language Distribution → Architecture Overview → API Summary → Database Schema → Technology Stack → Recommendations.

```python
generate_migration_report(project: Project) -> bytes
```
Sections: Cover → Migration Overview → Target Stack → Transformation Mappings table → Test Scripts → Next Steps checklist.

Both functions return raw PDF bytes which the API layer wraps in `StreamingResponse`.

**Enhancement:** Add charts (pie charts for language distribution, bar charts for confidence scores) using ReportLab's drawing module. Add a diff table showing changed file count per transformation mapping.

---

### 4.9 `backend/app/services/business_analyzer.py`

**Purpose:** Extract business rules and domain knowledge from code.

**Data classes:**
- `BusinessRule` — `rule_type` (validation/authorization/workflow/calculation/constraint), `description`, `location`, `confidence`, `code_snippet`, `impact`
- `BusinessProcess` — `name`, `description`, `steps`, `entities_involved`, `business_value`, `complexity`

```python
analyze_business_rules(files: list, parse_results: list) -> dict
```
Returns:
- `business_summary` — Narrative description of what the system does
- `domain_analysis` — Primary domain: e-commerce / finance / healthcare / HR / logistics / generic
- `business_rules` — List of `BusinessRule` objects extracted from validation annotations, `@PreAuthorize`, conditional business logic, calculation methods
- `business_processes` — Identified workflows (e.g., "order checkout process", "employee onboarding")
- `complexity_assessment` — LOW / MEDIUM / HIGH / VERY_HIGH based on rule count and interaction complexity

**Domain detection keywords:**

| Domain | Keywords |
|---|---|
| E-commerce | order, product, cart, payment, inventory, customer, checkout |
| Finance | account, transaction, payment, invoice, billing, ledger |
| Healthcare | patient, doctor, appointment, diagnosis, treatment, prescription |
| HR | employee, payroll, attendance, leave, performance, recruitment |

**Enhancement:** Feed business rules back into the transformation prompt so the LLM is explicitly told "this rule must be preserved." Add rule traceability — link each rule to the transformed output file.

---

### 4.10 `backend/app/services/database_analyzer.py`

**Purpose:** Parse SQL DDL and generate ORM models for target technology.

**Key classes:**
- `DDLParser` — Parses `CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE ADD CONSTRAINT FOREIGN KEY` statements
- `ORMGenerator` — Generates ORM code for SQLAlchemy, JPA/Hibernate, Django ORM
- `DatabaseAnalyzer` — Orchestrates parsing + generation

```python
parse_ddl_file(content: str, file_path: str) -> DatabaseSchema
```
Extracts: `tables` (with columns, data types, PKs), `indexes`, `foreign_keys`, `views`, `procedures`, `triggers`.

```python
generate_orm_models(schema: DatabaseSchema, target_orm: str) -> str
```
Produces ready-to-use model code. Example for SQLAlchemy:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    orders = relationship("Order", back_populates="user")
```

```python
generate_migration_scripts(old_schema, new_schema) -> dict
```
Produces `upgrade.sql` and `downgrade.sql` by diffing old vs new schema.

**Enhancement:** Integrate Alembic for Python projects to produce proper versioned migration files. Add Flyway/Liquibase XML generation for Java projects.

---

### 4.11 `backend/app/services/api_converter.py`

**Purpose:** Extract REST/SOAP endpoints and generate API documentation + framework conversion.

**Key classes:**
- `APIExtractor` — Detects endpoints using framework-specific patterns
- `APIConverter` — Converts endpoint definitions between frameworks

**Detection patterns:**

| Framework | Patterns |
|---|---|
| Spring Boot | `@RestController`, `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping` |
| Flask/FastAPI | `@app.route`, `@router.get`, `@app.post`, `@router.post` |
| Express | `router.get`, `app.post`, `router.use` middleware |
| ASP.NET | `[HttpGet]`, `[ApiController]`, `[Route]` |

```python
extract_apis(files: list, parse_results: list) -> dict
```
Returns:
- `endpoints` — List with path, HTTP method, handler, parameters, response models
- `models` — DTOs/request-response classes with properties and validation annotations

```python
generate_openapi_spec(endpoints: list, models: list) -> dict
```
Produces OpenAPI 3.0 JSON spec.

```python
generate_postman_collection(endpoints: list) -> dict
```
Produces Postman Collection v2.1 JSON with all endpoints pre-configured.

```python
generate_curl_examples(endpoints: list) -> list[str]
```
One cURL command per endpoint with example request body.

**Enhancement:** Add Swagger UI embedding in the frontend using `swagger-ui-react`. Generate TypeScript client SDK from the OpenAPI spec using `openapi-typescript`.

---

### 4.12 `backend/app/services/confidence_scoring.py`

**Purpose:** Calculate multi-dimensional confidence scores for analysis quality.

**Score categories (each 0.0–1.0):**

| Category | Weight | What it measures |
|---|---|---|
| PARSING | 15% | File success rate, language coverage, content quality |
| ANALYSIS | 20% | API/table detection coverage, pattern accuracy |
| PATTERN_DETECTION | 15% | Design patterns found, anti-patterns detected |
| ARCHITECTURE | 15% | Layer identification accuracy, component relationships |
| SECURITY | 10% | Vulnerability detection thoroughness |
| DEPENDENCIES | 15% | Import resolution, framework detection accuracy |
| RECOMMENDATIONS | 10% | Modernization path feasibility |
| OVERALL | — | Weighted average of all above |

**Output `ConfidenceScore` object:**
```python
@dataclass
class ConfidenceScore:
    category: str
    score: float          # 0.0 – 1.0
    reasoning: str
    evidence: list[str]   # specific facts that drove the score
    factors: dict         # sub-score breakdown
    metadata: dict
```

**Enhancement:** Add time-series tracking of confidence scores across pipeline re-runs. Expose per-file confidence so users can see which files had low-quality analysis.

---

### 4.13 `backend/app/services/behavioral_validation.py`

**Purpose:** Run a configurable set of validation gates; create human review requests when confidence is below threshold.

**Validators (all implement `BaseValidator`):**

| Validator | Gate condition |
|---|---|
| `ConfidenceValidator` | Overall confidence ≥ configured threshold (default 0.7) |
| `SecurityValidator` | No critical vulnerabilities detected |
| `ArchitectureValidator` | At least 2 architecture layers identified |
| `QualityGateValidator` | Average maintainability index ≥ threshold |
| `DependencyHealthValidator` | All key imports resolved |
| `FileCoverageValidator` | ≥ 90% of files successfully processed |
| `TransformationCompletenessValidator` | All transformation mappings have status `complete` |
| `TestCoverageReadinessValidator` | Test stubs generated for all modules |

**Human review gate logic:**
```
IF any validator fails:
    Create ReviewRequest with:
        priority = CRITICAL  (confidence < 0.3)
                   HIGH      (0.3 – 0.5)
                   MEDIUM    (0.5 – 0.7)
                   LOW       (> 0.7 but below threshold)
        expires_at = now + 60 minutes
        status = PENDING
ELSE:
    IF confidence > auto_approve_threshold (0.9):
        status = AUTO_APPROVED
    ELSE:
        pipeline continues
```

**Enhancement:** Add Slack/Teams webhook integration to notify reviewers when a `HIGH` or `CRITICAL` review request is created. Add reviewer assignment based on detected technology (e.g., assign Java expert when Java EE is detected).

---

### 4.14 `backend/app/services/test_generator.py`

**Purpose:** Generate test script templates for the modernized codebase.

```python
generate_test_scripts(transformed_files: list, selected_stack: dict, apis: list) -> list[dict]
```

Generates per-technology test suites:

| Technology | Test types generated |
|---|---|
| Java (Spring Boot) | JUnit 5 + RestAssured API tests, JUnit 5 + Mockito unit tests, Spring Boot Test + Testcontainers integration tests |
| Python (FastAPI/Django) | pytest + httpx API tests, pytest unit tests, pytest integration tests |
| Node.js (Express) | Jest + Supertest API tests, Jest unit tests |
| Any frontend | Playwright / Cypress E2E test stubs |
| Any DB | SQL test scripts for data validation |

**Enhancement:** Use the extracted business rules (from `business_analyzer.py`) to auto-generate test cases that verify business logic preservation, not just API contract.

---

### 4.15 `backend/app/services/enhanced_chunking.py`

**Purpose:** Semantically chunk source code for high-quality RAG embeddings.

**Chunk types:** FUNCTION, CLASS, MODULE, IMPORT, COMMENT, DOCUMENTATION, CONFIGURATION, TEST

```python
chunk_file(content: str, language: str, file_path: str) -> list[CodeChunk]
```
Routing:
- Python → `_chunk_python_ast()` using Python `ast` module
- Java → `_chunk_java_class()` using regex class/method extraction
- JavaScript/TypeScript → `_chunk_js_function()` for function/component extraction
- All others → `_chunk_generic()` sliding window (50 lines, 200 char overlap, max 2000 chars)

**`CodeChunk` fields:** `content`, `chunk_type`, `language`, `file_path`, `start_line`, `end_line`, `complexity_score`, `dependencies`, `metadata`

**Enhancement:** Add overlap between adjacent function chunks to capture inter-function context. Add cross-file dependency stitching so callers and callees end up in the same chunk group.

---

## 5. Backend — Agent System (LangGraph)

### 5.1 `backend/app/agents/base_agent.py`

**`BaseCodeMorphAgent`** — Abstract base class for all agents.

```python
async execute(input_data: dict) -> AgentResult
```
Calls `_format_input()` → builds LLM chain → runs tools → returns `AgentResult`.

```python
@abstractmethod _get_system_prompt() -> str
@abstractmethod _get_default_tools() -> list
@abstractmethod _format_input(input_data) -> str
```

**`AgentResult` dataclass:**
```python
@dataclass
class AgentResult:
    success: bool
    data: dict
    confidence: float
    reasoning: str
    errors: list[str]
    metadata: dict
```

**`CodeMorphCallbackHandler`** — LangChain callback handler. Logs every tool call and LLM action for audit purposes.

---

### 5.2 `backend/app/agents/analysis_agent.py`

**`CodeAnalysisAgent`** — Deep code quality analysis.

Tools available: `ASTAnalysisTool`, `ComplexityAnalysisTool`, `DependencyGraphTool`, `PatternDetectionTool`, `SecurityAnalysisTool`.

```python
analyze_single_file(file_content: str, language: str) -> AgentResult
```
Runs full analysis on one file. Used for high-value files (large classes, core services).

```python
analyze_architecture(files: list, parse_results: list) -> AgentResult
```
Runs architecture-level analysis across all files.

---

### 5.3 `backend/app/agents/context_agent.py`

**`ContextAnalysisAgent`** — Detects architectural patterns.

Identifies:
- **Frontend patterns** — SPA, MVC, micro-frontend
- **Business patterns** — CQRS, Event Sourcing, Saga
- **Data patterns** — Repository, Active Record, CQRS read models
- **Integration patterns** — Outbox, Anti-Corruption Layer, Adapter
- **Infrastructure patterns** — Circuit Breaker, Retry, Bulkhead

---

### 5.4 `backend/app/agents/tools/code_analysis_tools.py`

All tools inherit from LangChain `BaseTool` and are directly usable in agent chains.

| Tool | Input | Output |
|---|---|---|
| `ASTAnalysisTool` | `{code, language}` | Classes, functions, imports, exports as structured dict |
| `ComplexityAnalysisTool` | `{code, language}` | Cyclomatic complexity, cognitive complexity, nesting depth |
| `DependencyGraphTool` | `{files}` | Adjacency list of module dependencies |
| `PatternDetectionTool` | `{code, language}` | Detected design patterns and anti-patterns |
| `SecurityAnalysisTool` | `{code, language}` | Vulnerability list with severity (CRITICAL/HIGH/MEDIUM/LOW) |

**Enhancement:** Add `PerformanceAnalysisTool` to flag N+1 queries, unbounded loops, synchronous I/O in async contexts. Add `LicenseComplianceTool` to detect open-source license obligations.

---

### 5.5 `backend/app/agents/orchestrator.py`

**`CodeMorphOrchestrator`** — LangGraph-based multi-agent workflow engine.

**Workflow graph:**
```
initialize
  → context_analysis        (ContextAnalysisAgent)
  → code_analysis           (CodeAnalysisAgent)
  → dependency_analysis     (DependencyGraphTool)
  → database_analyzer       (DatabaseAnalyzer service)
  → api_analyzer            (APIConverter service)
  → confidence_scoring      (ConfidenceScoring service)
  → generate_recommendations (Recommender service)
  → [conditional]
       IF confidence < threshold → human_review_gate
       ELSE                      → validation
  → validation              (BehavioralValidation engine)
  → finalize
```

**`OrchestrationConfig`:**
```python
@dataclass
class OrchestrationConfig:
    enable_human_review: bool = True
    confidence_threshold: float = 0.7
    max_retries: int = 3
    parallel_execution: bool = True
    validation_gates: list[str] = [...]
    enable_database_analysis: bool = True
    enable_api_conversion: bool = True
    enable_behavioral_validation: bool = True
```

```python
async orchestrate(files: list, project_context: dict, analysis_type: str) -> dict
```
Returns comprehensive result with: `confidence_scores`, `recommendations`, `validation_results`, `audit_trail`, `agent_outputs`.

**Enhancement:** Add parallel execution for independent stages (database_analyzer and api_analyzer can run concurrently). Add a `dry_run` mode that simulates the pipeline without writing to DB.

---

## 6. Backend — Embeddings & Vector Store

### 6.1 `backend/app/embeddings/embedder.py`

```python
get_embedding_model(model_name: str = "BAAI/bge-small-en") -> SentenceTransformer
```
Loads model on first call, caches in memory for subsequent calls. 384-dimensional embeddings.

```python
generate_embeddings(texts: list[str]) -> np.ndarray
```
Batch encodes using sentence-transformers `encode()`. Returns numpy array of shape `(N, 384)`.

```python
generate_embedding(text: str) -> np.ndarray
```
Single text → 384-dim vector.

---

### 6.2 `backend/app/embeddings/vector_store.py`

**`VectorStore` class:**

```python
add_documents(texts: list[str], metadatas: list[dict], embeddings: np.ndarray)
```
Adds to FAISS `IndexFlatIP` (inner product = cosine on normalized vectors).

```python
search(query_embedding: np.ndarray, top_k: int = 5) -> list[dict]
```
Returns top-K similar documents with scores and metadata (file_path, language, chunk_type, line numbers).

```python
save() / load()
```
Persists FAISS index + metadata to `data/vector_stores/{project_id}/`.

```python
build_vector_store(project_id: str, files: list, parse_results: list) -> VectorStore
```
Full pipeline: chunk all files → generate embeddings in batches → build FAISS index → save to disk.

```python
get_rag_retriever(project_id: str) -> callable
```
Returns a retriever function `(query: str) -> list[dict]` that embeds the query on-the-fly and searches.

**Enhancement:** Switch to FAISS `IndexIVFFlat` for projects with > 50k chunks (much faster approximate search). Add metadata filtering (e.g., retrieve only chunks from a specific layer).

---

## 7. Backend — Database Layer

### 7.1 `backend/app/database/db.py`

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/codemorph.db"
engine = create_engine(url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]
```
FastAPI dependency — yields a session, closes on exit.

```python
def init_db()
```
Called at startup from `main.py`. Runs `Base.metadata.create_all(engine)`.

---

### 7.2 `backend/app/models/project.py`

**Key ORM models:**

| Model | Key fields | Relationships |
|---|---|---|
| `Project` | id (UUID), name, path, status, total_files, total_loc, language_distribution (JSON), detected_stack (JSON), selected_stack (JSON), transformation_progress (JSON), test_scripts (JSON) | → PipelineRun, AnalysisResult, ParsedFile, ContextElement, TransformedFile |
| `PipelineRun` | stage, progress (0–100), message, started_at, completed_at | → Project |
| `ParsedFile` | file_path, language, framework, ast_data (JSON), functions (JSON), classes (JSON), imports (JSON), lines_of_code, complexity_score, maintainability_index, content_hash | → Project |
| `ContextElement` | element_type, layer, technologies (JSON), dependencies (JSON), confidence_score, complexity_level | → Project |
| `AnalysisResult` | result_type, data (JSON) | → Project |
| `TransformedFile` | original_path, transformed_path, source_tech, target_tech, content, transformation_notes | → Project |
| `DatabaseAnalysisResult` | tables_count, tables_data (JSON), relationships (JSON), orm_models (JSON), migration_scripts (JSON) | → Project |
| `APIAnalysisResult` | endpoints_count, endpoints_data (JSON), openapi_spec (JSON), postman_collection (JSON), curl_examples (JSON) | → Project |
| `ValidationResult` | validation_type, status, score, threshold, passed, evidence (JSON), recommendations (JSON) | → Project |
| `ReviewRequest` | title, description, priority, status, expires_at, assigned_to, decision_reason | → Project |

**All tables use cascade delete** — deleting a project removes all child records automatically.

**Enhancement:** Migrate from SQLite to PostgreSQL for production use. Add `updated_at` trigger columns for all tables. Add soft-delete (`deleted_at`) to `Project` to enable recovery.

---

## 8. Frontend — Pages & Components

### 8.1 `frontend/src/main.tsx`

React 19 entry point. Mounts `<App />` into `#root` using `ReactDOM.createRoot`.

---

### 8.2 `frontend/src/App.tsx`

Sets up global providers and routing.

```tsx
<QueryClientProvider client={queryClient}>
  <ThemeProvider theme={theme}>
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Dashboard />} />
          <Route path="/project/:id" element={<ProjectDetail />} />
          <Route path="/project/:id/context-built" element={<ProjectDetail tab="context" />} />
          <Route path="/project/:id/stack" element={<ProjectDetail tab="stack" />} />
          <Route path="/project/:id/select-stack" element={<ProjectDetail tab="select" />} />
          <Route path="/project/:id/transformation" element={<ProjectDetail tab="transformation" />} />
          <Route path="/project/:id/database-analysis" element={<ProjectDetail tab="database" />} />
          <Route path="/project/:id/api-analysis" element={<ProjectDetail tab="api" />} />
          <Route path="/project/:id/validation" element={<ProjectDetail tab="validation" />} />
        </Routes>
      </Router>
    </ToastProvider>
  </ThemeProvider>
</QueryClientProvider>
```

**Enhancement:** Add a protected route wrapper with auth guard for multi-user deployments. Add a `<Suspense>` boundary around each route with skeleton loaders.

---

### 8.3 `frontend/src/pages/Dashboard.tsx`

Project management home page.

**State:**
- `searchQuery` — filter by name/path/description
- `statusFilter` — all / running / complete / error
- `sortOrder` — newest / oldest / largest

**TanStack Query hooks:**
```tsx
const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: api.listProjects,
  refetchInterval: hasRunningPipelines ? 5000 : false
})
const createMutation = useMutation({ mutationFn: api.createProject, ... })
const deleteMutation = useMutation({ mutationFn: api.deleteProject, ... })
```

**UI sections:**
- Stats bar (total projects, running pipelines, total LOC)
- Search + filter + sort bar
- Project cards grid with status badges, file counts, language chips
- Create project dialog (name, path, description)
- Delete confirmation dialog

**Enhancement:** Add drag-and-drop folder picker instead of text path input. Add project duplication. Add bulk delete with multi-select.

---

### 8.4 `frontend/src/pages/ProjectDetail.tsx`

Main analysis workspace — tabbed interface covering all pipeline stages.

**Tabs:**
0. **Overview** — Status, language distribution donut, detected stack chips
1. **Context Built** — Architecture layer tree, component list, dependency graph
2. **Stack Detection** — Table of detected technologies with confidence progress bars
3. **Select Stack** — Radio button groups per category, "Start Transformation" CTA
4. **Transformation** — Mapping table with per-mapping progress, transformed file count
5. **Database Analysis** — Schema table viewer, ORM model code display, relationship graph
6. **API Analysis** — Endpoint explorer, OpenAPI spec viewer, Postman export button
7. **Validation** — Validation gate results, review request queue, approval workflow

**Query:**
```tsx
const { data: project } = useQuery({
  queryKey: ['project', id],
  queryFn: () => api.getProject(id),
  refetchInterval: isActive ? 2000 : false  // poll while pipeline running
})
```

**Key interactions:**
- **Start Pipeline** → `api.startPipeline(id)` → mutation → toast notification
- **Select Stack** → collects radio values → `api.selectStack(id, selections)` → advances to transforming
- **Download Report** → `window.open(api.downloadLegacyReport(id))`
- **Restart From Stage** → dialog + `api.restartFrom(id, stage)`
- **Submit Review** → `api.submitReviewDecision(requestId, {decision, notes})`

**Enhancement:** Add a side-by-side diff viewer for transformed files. Add a "what changed" summary card per transformation mapping. Add animated pipeline stage indicator showing real-time progress.

---

### 8.5 `frontend/src/components/AppShell.tsx`

Global layout wrapper.

- **Header:** Logo, breadcrumb, notification icon, help icon
- **Content area:** `max-width: 1400px`, centered, min-height with header offset
- **Footer:** Version, links

**Enhancement:** Add a persistent notification center drawer showing all human review requests across projects. Add dark mode toggle.

---

### 8.6 `frontend/src/components/DatabaseAnalysis.tsx`

Database schema display component.

- Tables accordion (name, column count, PK indicator)
- Per-table column detail (name, type, nullable, default)
- Foreign key relationship display
- Generated ORM models code block with syntax highlighting
- Migration scripts expandable section

---

### 8.7 `frontend/src/components/APIAnalysis.tsx`

API explorer component.

- Endpoints table (method chip, path, handler, parameter count)
- Request/response model display
- OpenAPI spec JSON viewer
- "Download Postman Collection" button → triggers JSON file download
- cURL examples expandable per endpoint

---

### 8.8 `frontend/src/components/ValidationDashboard.tsx`

Human review and validation gate UI.

- Summary bar: total gates / passed / failed / pending
- Per-gate result row with: name, status icon, confidence score, threshold, pass/fail chip
- `ReviewRequest` cards: priority badge, title, expiry countdown, approve/reject buttons
- Approval notes textarea before submit

---

### 8.9 `frontend/src/components/ToastProvider.tsx`

Toast notification context.

```tsx
const { showToast } = useToast()
showToast('Stack selected successfully', 'success')
showToast('Pipeline failed: connection refused', 'error')
```

Auto-dismisses after 4 seconds. Stacks multiple toasts vertically.

---

## 9. Frontend — API Client

### `frontend/src/api.ts`

Single file containing all typed API functions. Base URL: `/api` (proxied by Vite dev server to `localhost:8000`).

**Pattern:** Each function is `async () => response.json()` with typed return. No global error handling — errors surface to TanStack Query's error state.

**All functions:**

```typescript
// Projects
listProjects(): Promise<ProjectSummary[]>
getProject(id: string): Promise<Project>
createProject(data: CreateProjectInput): Promise<Project>
updateProject(id: string, data: UpdateProjectInput): Promise<Project>
deleteProject(id: string): Promise<{ detail: string }>

// Pipeline
startPipeline(id: string): Promise<{ detail: string }>
getStatus(id: string): Promise<PipelineStatus>
selectStack(id: string, selections: Record<string, string>): Promise<{ detail: string }>
restartFrom(id: string, stage: string): Promise<{ detail: string }>
cancelPipeline(id: string): Promise<{ detail: string }>

// Reports & Artifacts
downloadLegacyReport(id: string): string  // returns URL for window.open
downloadMigrationReport(id: string): string
downloadArtifacts(id: string): string

// Enhanced Analysis
startDatabaseAnalysis(id: string): Promise<{ detail: string }>
getDatabaseAnalysis(id: string): Promise<DatabaseAnalysis>
startAPIAnalysis(id: string): Promise<{ detail: string }>
getAPIAnalysis(id: string): Promise<APIAnalysis>

// Validation
getValidationResults(projectId: string): Promise<ValidationResultDetail[]>
getValidationDashboard(projectId?: string): Promise<ValidationDashboard>
submitReviewDecision(requestId: string, decision: ReviewDecision): Promise<ReviewResponse>
getValidationMetrics(projectId?: string): Promise<ValidationMetrics>
configureValidationCriteria(criteria: ValidationCriteria): Promise<{ success: boolean }>

// Orchestration
getOrchestratorStatus(id: string): Promise<OrchestratorStatus>
getAuditReport(id: string): Promise<AuditReport>
```

**Enhancement:** Add a global `fetch` interceptor to handle 401/403 for auth. Add request cancellation via `AbortController` so stale queries are cancelled when navigating away.

---

## 10. Key Algorithms

### 10.1 Confidence Scoring Formula

```
Overall = Σ (category_score × weight)

Parsing Score (weight 0.15):
  = 0.40 × (files_processed / total_files)
  + 0.30 × (supported_languages / total_languages)
  + 0.20 × min(avg_file_size / 10000, 1.0)
  + 0.10 × content_quality_heuristic

Analysis Score (weight 0.20):
  = 0.40 × api_detection_rate
  + 0.40 × table_detection_rate
  + 0.20 × entity_mapping_accuracy
```

### 10.2 Stack Detection Algorithm

```
For each technology T in category C:
  evidence = 0

  # Import/annotation matching (highest weight × 3)
  for each parsed file:
    if T.import_pattern in file.imports:
      evidence += 3

  # Config file detection (weight × 2)
  if T.config_file in project_files:
    evidence += 2

  # Dependency declaration (weight × 2)
  if T.dependency_pattern in package_manager_files:
    evidence += 2

  # File extension count (weight × 1)
  evidence += count(files matching T.extension_pattern) × 0.1

confidence = min(evidence / T.max_expected_evidence, 1.0) × 100
include if confidence > 20
```

### 10.3 RAG Retrieval Flow

```
1. BUILD INDEX (once per project, after parsing):
   chunks = enhanced_chunking.chunk_all_files(files)
   embeddings = embedder.generate_embeddings([c.content for c in chunks])
   faiss_index = IndexFlatIP(384)
   faiss_index.add(normalize(embeddings))
   save to data/vector_stores/{project_id}/

2. RETRIEVAL (per transformation task):
   query = f"Transform {source_tech} code handling {transformation_type}"
   q_embedding = embedder.generate_embedding(query)
   q_normalized = normalize(q_embedding)
   distances, indices = faiss_index.search(q_normalized, top_k=5)
   context_chunks = [chunks[i] for i in indices[0]]

3. AUGMENTATION:
   prompt = system_prompt
         + "\n\nRelevant existing code patterns:\n"
         + "\n---\n".join(c.content for c in context_chunks)
         + "\n\nSource code to transform:\n"
         + file_content
```

---

## 11. Configuration & Environment

**Backend environment file:** `backend/.env`

```env
# Required for LLM transformation
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional overrides
DATABASE_URL=sqlite:///./data/codemorph.db
VECTOR_STORE_PATH=./data/vector_stores
ARTIFACTS_PATH=./data/artifacts
CONFIDENCE_THRESHOLD=0.7
AUTO_APPROVE_THRESHOLD=0.9
```

**Frontend proxy config (`vite.config.ts`):**
```ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

**CORS origins allowed:** `http://localhost:5173`, `http://localhost:3000`, `http://127.0.0.1:5173`

---

## 12. Enhancement & Integration Opportunities

### 12.1 LLM Provider Flexibility

Currently hardcoded to Azure OpenAI. Add a provider abstraction:

```python
# services/llm_provider.py
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list, **kwargs) -> str: ...

class AzureOpenAIProvider(LLMProvider): ...
class AnthropicProvider(LLMProvider): ...   # Claude API
class BedrockProvider(LLMProvider): ...
```

Integrate via `langchain-anthropic` package using `claude-sonnet-4-6` for transformation tasks.

---

### 12.2 WebSocket Real-time Updates

Replace 2-second polling with WebSocket push:

```python
# backend/app/api/ws.py
@app.websocket("/ws/projects/{project_id}/status")
async def pipeline_status_ws(websocket: WebSocket, project_id: str):
    await manager.connect(websocket, project_id)
    try:
        while True:
            await asyncio.sleep(0.5)
            status = get_current_status(project_id)
            await websocket.send_json(status)
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
```

Frontend switch from `refetchInterval` to `useWebSocket` hook.

---

### 12.3 Authentication & Multi-Tenancy

Add JWT-based auth with per-user project isolation:

```python
# Add to Project model
owner_id = Column(String, ForeignKey("users.id"), nullable=False)
is_public = Column(Boolean, default=False)
```

Use `fastapi-users` library for user management. Filter all queries by `current_user.id`.

---

### 12.4 Git Integration

Add native Git workflow integration:

```python
# After transformation completes:
POST /api/projects/{id}/create-branch
  → Creates a new branch in the source repo
  → Commits transformed files
  → Optionally opens a PR via GitHub/GitLab API

GET /api/projects/{id}/diff
  → Returns unified diff between original and transformed files
```

---

### 12.5 Mermaid Architecture Diagrams

Export architecture as renderable diagrams:

```python
# In context_builder.py
def to_mermaid_diagram(context: dict) -> str:
    lines = ["graph TD"]
    for dep_from, deps in context["dependencies"].items():
        for dep_to in deps:
            lines.append(f"  {dep_from} --> {dep_to}")
    return "\n".join(lines)
```

Render in UI using `mermaid.js` or embed in PDF reports.

---

### 12.6 PostgreSQL Migration

For production scale:

```python
# Switch DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:pass@host/codemorph

# Replace FAISS with pgvector for unified storage
CREATE EXTENSION vector;
ALTER TABLE parsed_files ADD COLUMN embedding vector(384);
CREATE INDEX ON parsed_files USING ivfflat (embedding vector_cosine_ops);
```

---

### 12.7 Streaming Transformation Progress

Currently transformation is all-or-nothing. Add streaming:

```python
# SSE endpoint
GET /api/projects/{id}/transform/stream
  → Server-Sent Events
  → Emits one event per file transformed: {file, status, preview}
```

Frontend shows a live file-by-file transformation feed.

---

### 12.8 Business Rule Preservation Tests

Wire business rules into test generation:

```python
# In test_generator.py
for rule in business_rules:
    if rule.rule_type == "validation":
        generate_validation_test(rule, target_framework)
    elif rule.rule_type == "authorization":
        generate_auth_test(rule, target_framework)
```

Ensures regression tests specifically cover detected business logic.

---

### 12.9 Notification Integrations

For the human review gate, add outbound notifications:

```python
# services/notifications.py
class SlackNotifier:
    async def notify_review_request(self, review_request: ReviewRequest): ...

class TeamsNotifier:
    async def notify_review_request(self, review_request: ReviewRequest): ...

class EmailNotifier:
    async def notify_review_request(self, review_request: ReviewRequest): ...
```

Configure via `.env`: `NOTIFICATION_PROVIDER=slack`, `SLACK_WEBHOOK_URL=...`

---

### 12.10 CLI Interface

Add a `codemorph` CLI for CI/CD pipelines:

```bash
codemorph analyze ./legacy-app --target spring-boot,react,postgresql
codemorph transform ./legacy-app --project-id abc123
codemorph report ./legacy-app --format pdf --output ./reports/
```

Built with `typer` or `click`, calling the same services directly without FastAPI overhead.

---

*Generated by deep codebase scan — 2026-04-09*

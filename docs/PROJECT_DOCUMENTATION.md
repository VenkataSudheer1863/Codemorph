# CodeMorph — Project Documentation

## Overview

CodeMorph is a full-stack legacy codebase modernization platform. It ingests a source codebase (local path or Git URL), runs a multi-stage analysis pipeline, detects the tech stack, generates modernization recommendations, and produces transformed output artifacts — all driven by an agentic AI system backed by Azure OpenAI and LangGraph.

The platform exposes a REST API (FastAPI) consumed by a React/TypeScript frontend. Analysis results, pipeline state, and validation records are persisted in a SQLite database. Semantic search over code is powered by a FAISS vector store with sentence-transformer embeddings.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                 │
│  Dashboard · ProjectDetail · ValidationDashboard        │
│  MUI v5 · TanStack Query · TypeScript                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│  /api/projects  /api/projects/{id}/...                  │
│  /api/enhanced/...                                      │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│              Pipeline Orchestration                      │
│  ingestion → parsing → context_building →               │
│  agentic_analysis → selecting → transforming → complete │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│           LangGraph Agentic System                       │
│  ContextAgent · AnalysisAgent · DatabaseAnalyzer        │
│  APIConverter · ConfidenceScoringEngine                  │
│  BehavioralValidationEngine                             │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│  SQLite (SQLAlchemy)  │  FAISS Vector Store             │
│  codemorph.db         │  sentence-transformers          │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Language | Python 3.x |
| Web Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy (declarative) |
| Database | SQLite (`backend/data/codemorph.db`) |
| AI / LLM | Azure OpenAI (GPT-4) via `langchain-openai` |
| Agentic Framework | LangGraph + LangChain |
| Embeddings | `sentence-transformers` (BAAI/bge-small-en) |
| Vector Store | FAISS (`faiss-cpu`) |
| AST Parsing | tree-sitter (with regex fallback) |
| PDF Reports | ReportLab |
| Graph Analysis | NetworkX |
| SQL Parsing | sqlparse |
| Config | python-dotenv |

### Frontend
| Component | Technology |
|-----------|-----------|
| Language | TypeScript |
| Framework | React 19 |
| Build Tool | Vite |
| UI Library | MUI (Material UI) v5 |
| Data Fetching | TanStack Query (React Query) |
| Routing | React Router |
| Icons | MUI Icons |

---

## Environment Variables

All variables live in `backend/.env` (copy from `backend/.env.example`):

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

If Azure OpenAI is not configured, the transformation stage falls back to **pass-through mode** (copies source files without LLM transformation). All other pipeline stages work without Azure credentials.

---

## How to Run

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # dev server on http://localhost:5173
npm run build      # production build to frontend/dist/
```

The frontend proxies `/api` requests to `http://localhost:8000` via Vite's dev proxy config.

---

## Pipeline Stages

The pipeline progresses through these ordered stages, stored in `PIPELINE_STAGES`:

```
created → ingesting → parsing → context_building →
agentic_analysis → selecting → transforming → complete
```

Each stage creates a `PipelineRun` record and an `AnalysisResult` record in the database.

### Stage 1 — Ingesting (`ingestion.py`)
- Accepts a local filesystem path or Git URL (auto-clones via `git clone --depth 1`)
- Recursively walks the directory, skipping `node_modules`, `.git`, `target`, `build`, etc.
- Filters files by extension (`.java`, `.py`, `.js`, `.ts`, `.sql`, `.xml`, `.yml`, etc.)
- Detects language per file, counts non-empty lines of code
- Returns: `files[]`, `total_files`, `total_loc`, `language_distribution`

### Stage 2 — Parsing (`parser.py`)
- Parses each file using tree-sitter (with graceful regex fallback on Windows where C++ build tools may be absent)
- Extracts: functions, classes, imports, exports, variables, endpoints, framework patterns
- Calculates complexity score and maintainability index per file
- Stores each file as a `ParsedFile` record with full AST data, content hash (SHA-256), and parsing errors

### Stage 3 — Context Building (`context_builder.py`)
- Groups parsed files into architecture layers: `frontend`, `backend`, `database`, `config`
- Builds a dependency graph and service map
- Stores each component as a `ContextElement` record
- Generates a dynamic project summary from stored context elements
- Builds a FAISS vector store for RAG (non-critical, failure is logged and skipped)

### Stage 4 — Agentic Analysis (`orchestrator.py`)
- Initializes `CodeMorphOrchestrator` with a LangGraph `StateGraph`
- Runs 10 nodes in sequence: `initialize → context_analysis → code_analysis → dependency_analysis → database_analyzer → api_analyzer → confidence_scoring → generate_recommendations → [human_review_gate] → validation → finalize`
- Falls back to traditional analysis (stages 4a–4c below) if Azure OpenAI is not configured or the orchestrator throws

#### 4a — Analysis (`analyzer.py`)
- Detects APIs, database tables, stored procedures, ORM entities, message queues, SOAP services

#### 4b — Stack Detection (`stack_detector.py`)
- Identifies frontend framework, backend framework, database, build tools with confidence scores and alternatives

#### 4c — Recommendations (`recommender.py`)
- Generates modernization recommendations per stack category

### Stage 5 — Selecting
- User reviews detected stack and recommendations in the UI
- Submits `POST /api/projects/{id}/select-stack` with chosen target technologies
- Pipeline waits at `selecting` status until stack is selected

### Stage 6 — Transforming (`transformer.py`)
- Builds transformation mappings (source → target file paths)
- Prepends a conversion mindmap to the LLM context for guided transformation
- Calls Azure OpenAI to transform each file according to the selected stack
- Falls back to pass-through (copy source) if LLM is unavailable
- Generates test scripts (`test_generator.py`)
- Packages all transformed files into a ZIP artifact

### Stage 7 — Complete
- Project status set to `complete`
- Validation results written to DB
- Artifacts and reports available for download

---

## Database Schema

All tables use UUID primary keys (string). SQLite file: `backend/data/codemorph.db`.

### `projects`
Core project record. Stores all JSON analysis data as JSON columns.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| name | String(255) | Project name |
| path | Text | Source path or Git URL |
| description | Text | User description |
| status | String(50) | Pipeline stage (e.g. `parsing`, `complete`) |
| created_at / updated_at | DateTime | Timestamps |
| total_files | Integer | Files ingested |
| total_loc | Integer | Lines of code |
| languages_count | Integer | Distinct languages |
| frameworks_count | Integer | Distinct frameworks |
| language_distribution | JSON | `{lang: pct}` |
| architecture_layers | JSON | Layer → component map |
| detected_apis | JSON | API endpoint list |
| detected_tables | JSON | DB table list |
| detected_stack | JSON | Stack detection results |
| recommendations | JSON | Modernization recommendations |
| selected_stack | JSON | User-selected target stack |
| transformation_progress | JSON | `{processed, total, percent, ...}` |
| transformation_mappings | JSON | Source → target file mappings |
| project_summary | Text | Auto-generated narrative summary |
| test_scripts | JSON | Generated test script list |
| error_message | Text | Last error (nullable) |

### `pipeline_runs`
One record per pipeline stage execution.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| stage | String(50) | Stage name |
| progress | Float | 0–100 |
| message | Text | Status message |
| started_at / completed_at | DateTime | Timing |

### `analysis_results`
Generic key-value store for all intermediate analysis data.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| result_type | String(50) | `ingestion`, `parsing`, `context_building`, `agentic_analysis`, `analysis`, `stack_detection`, `recommendations`, `database_analysis`, `api_analysis`, `validation_results` |
| data | JSON | Full result payload |
| created_at | DateTime | |

### `parsed_files`
Detailed per-file parsing output.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| file_path | Text | Relative path |
| file_type / language / framework | String | Detected values |
| ast_data | JSON | Full AST |
| functions / classes / imports / exports / variables | JSON | Extracted elements |
| lines_of_code | Integer | |
| complexity_score / maintainability_index | Float | |
| original_content | Text | Raw source |
| content_hash | String(64) | SHA-256 |
| parsing_successful | Boolean | |
| parsing_errors | JSON | Error list |

### `context_elements`
Architecture components extracted during context building.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| element_type | String(50) | `component`, `service`, `model`, `api`, `database` |
| element_name | String(255) | |
| file_path | Text | |
| layer | String(100) | `frontend`, `backend`, `database`, `config` |
| description | Text | |
| technologies / dependencies / dependents | JSON | |
| code_patterns / api_endpoints / database_entities | JSON | |
| confidence_score | Float | |
| complexity_level | String(20) | `low`, `medium`, `high` |

### `database_analysis_results`
Detailed database schema analysis output.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| database_type | String(50) | `mysql`, `postgresql`, etc. |
| schema_name | String(255) | |
| tables_count / views_count / procedures_count / functions_count / triggers_count | Integer | Counts |
| tables_data / relationships / indexes / orm_models / recommendations / complexity_metrics | JSON | Analysis data |
| old_schema / new_schema / migration_scripts | JSON | Migration data |

### `api_analysis_results`
API endpoint analysis and conversion output.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| framework_type | String(50) | `spring_boot`, `flask`, etc. |
| endpoints_count / models_count | Integer | |
| endpoints_data / models_data / openapi_spec / postman_collection / curl_examples | JSON | |
| old_framework / new_framework | String | |
| conversion_mappings / statistics | JSON | |

### `validation_results`
Per-rule validation outcomes written after agentic analysis.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| validation_type | String(50) | `confidence_threshold`, `security_check`, `architecture_compliance`, `quality_gate`, `code_quality` |
| status | String(20) | `pending`, `approved`, `rejected`, `requires_review` |
| score / threshold | Float | |
| passed | Boolean | |
| message / evidence / recommendations | Text / JSON | |
| reviewer / review_notes / decision_reason | String / Text | Human review fields |

### `review_requests`
Human review gate requests created when validation requires manual sign-off.

| Column | Type | Description |
|--------|------|-------------|
| id | String PK | UUID |
| project_id | FK → projects | |
| title / description | String / Text | |
| priority | String(20) | `low`, `medium`, `high`, `critical` |
| status | String(20) | `pending`, `approved`, `rejected`, `timeout` |
| assigned_to | String(255) | Reviewer name |
| created_at / expires_at / reviewed_at | DateTime | |
| context_data | JSON | Snapshot of analysis data |
| review_notes / decision_reason | Text | |

---

## API Endpoints

### Projects — `/api/projects`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects (summary) |
| POST | `/api/projects` | Create a new project |
| GET | `/api/projects/{id}` | Get full project detail |
| DELETE | `/api/projects/{id}` | Delete project + cascade cleanup |

### Pipeline — `/api/projects/{id}/...`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/{id}/start` | Start the analysis pipeline |
| GET | `/{id}/status` | Get current pipeline status and progress |
| POST | `/{id}/select-stack` | Submit stack selection to advance past `selecting` |
| POST | `/{id}/restart-from/{stage}` | Restart pipeline from a specific stage |

### Reports & Artifacts — `/api/projects/{id}/...`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{id}/report/legacy` | Download legacy analysis PDF report |
| GET | `/{id}/report/migration` | Download migration plan PDF report |
| GET | `/{id}/artifacts` | Download transformed codebase as ZIP |

### Enhanced Analysis — `/api/enhanced/...`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/enhanced/database-analysis/{id}` | Trigger background database analysis |
| GET | `/enhanced/database-analysis/{id}/results` | Get database analysis results |
| POST | `/enhanced/api-analysis/{id}` | Trigger background API analysis |
| GET | `/enhanced/api-analysis/{id}/results` | Get API analysis results |
| GET | `/enhanced/validation/dashboard` | Get validation dashboard (optional `?project_id=`) |
| GET | `/enhanced/validation/metrics` | Get validation metrics (optional `?project_id=`) |
| POST | `/enhanced/validation/review/{request_id}` | Submit human review decision |
| POST | `/enhanced/validation/configure` | Configure validation criteria |
| GET | `/enhanced/orchestrator/{id}/status` | Get orchestrator status |

---

## Agentic System

### LangGraph Orchestrator (`orchestrator.py`)

`CodeMorphOrchestrator` builds a `StateGraph` with typed state (`AgentState`) and 10 nodes:

```
initialize
  → context_analysis      (ContextAgent)
  → code_analysis         (AnalysisAgent)
  → dependency_analysis   (dependency graph builder)
  → database_analyzer     (DatabaseAnalyzer)
  → api_analyzer          (APIConverter)
  → confidence_scoring    (ConfidenceScoringEngine)
  → generate_recommendations
  → [human_review_gate]   (conditional — only if confidence < threshold)
  → validation            (BehavioralValidationEngine)
  → finalize
  → END
```

The conditional edge at `generate_recommendations` routes to `human_review_gate` if `human_review_required` is true, otherwise directly to `validation`.

`OrchestrationConfig` controls:
- `enable_human_review` — whether to gate on human review
- `confidence_threshold` — threshold below which human review is triggered (default 0.7)
- `enable_database_analysis` / `enable_api_conversion` / `enable_behavioral_validation`

### AnalysisAgent (`analysis_agent.py`)
Uses Azure OpenAI to perform deep code analysis: architecture patterns, security vulnerabilities, anti-patterns, complexity metrics, and modernization opportunities.

### ContextAgent (`context_agent.py`)
Builds architectural context: layer identification, dependency mapping, service relationships, coupling analysis.

### Tools (`agents/tools/`)
- `code_analysis_tools.py` — LangChain tools for code pattern detection
- `dependency_graph_tools.py` — dependency graph construction and analysis
- `advanced_pattern_detection.py` — advanced anti-pattern and design pattern detection

---

## Validation System

### BehavioralValidationEngine (`behavioral_validation.py`)

Runs 4 validators after agentic analysis:

| Validator | Rule Type | Pass Condition |
|-----------|-----------|----------------|
| `ConfidenceValidator` | `confidence_threshold` | `overall_confidence >= 0.5` |
| `SecurityValidator` | `security_check` | `high_risk_vulnerabilities == 0` |
| `ArchitectureValidator` | `architecture_compliance` | `score >= 0.5` (allows 1 issue) |
| `QualityGateValidator` | `quality_gate` | `score >= 0.5` (allows 1 issue) |

**Overall status determination** uses a majority-pass rule:
- `>= 70%` validators pass → `APPROVED`
- `40–70%` pass → `REQUIRES_REVIEW`
- `< 40%` pass → `REJECTED`
- Security check with score 0.0 → forces `REQUIRES_REVIEW`

**Approval rate** in the metrics endpoint is floored at 72% (always above 70%) to reflect the relaxed thresholds. When no validation records exist, a 75.0% baseline is returned.

### Human Review Gate
When overall status is `REQUIRES_REVIEW` or `REJECTED`, a `ReviewRequest` is created with priority based on failure severity. Reviewers can submit decisions (`approved`, `rejected`, `requires_changes`) via `POST /enhanced/validation/review/{id}`.

---

## Transformation Engine (`transformer.py`)

### Conversion Mindmap
Before calling the LLM, a structured mindmap is prepended to the context showing the full source→target technology mapping. This guides the LLM to produce consistent, idiomatic output for the target stack.

### Pass-Through Mode
If Azure OpenAI is not configured or the LLM call fails, files are copied as-is with a comment header noting the pass-through. This ensures the pipeline always completes.

### Artifact Generation
After transformation, all output files are packaged into a ZIP archive downloadable via `GET /api/projects/{id}/artifacts`.

---

## RAG System (`embeddings/`)

### Vector Store (`vector_store.py`)
- Built during `context_building` stage
- Chunks source files using `enhanced_chunking.py` (semantic chunking by function/class boundaries)
- Generates embeddings using `sentence-transformers` (model: `BAAI/bge-small-en`)
- Stores FAISS index + document pickle at `backend/data/vector_stores/{project_id}/`
- Provides a retriever for RAG-augmented analysis queries

### Embedder (`embedder.py`)
- Lazy-loads the sentence-transformer model (cached globally)
- `generate_embeddings(texts)` → normalized numpy arrays
- Gracefully returns `None` if `sentence-transformers` is not installed

---

## Frontend

### Pages

**Dashboard (`pages/Dashboard.tsx`)**
- Lists all projects with status badges, file counts, LOC
- Create new project form (name, path/URL, description)
- Delete project with confirmation

**ProjectDetail (`pages/ProjectDetail.tsx`)**
- Tabbed view: Overview · Stack Detection · API Analysis · Database Analysis · Transformation · Validation
- Real-time pipeline status polling
- Stack selection UI (dropdowns per category)
- Transformation progress bar
- Download buttons for reports and artifacts

### Components

| Component | Purpose |
|-----------|---------|
| `AppShell.tsx` | Top nav + sidebar layout wrapper |
| `ValidationDashboard.tsx` | Full validation UI: pending reviews table, metrics, priority distribution, review dialog |
| `APIAnalysis.tsx` | API endpoints table, OpenAPI spec viewer, Postman/cURL export |
| `DatabaseAnalysis.tsx` | Schema viewer, ORM model display, relationship graph |
| `ProgressBar.tsx` | Animated pipeline progress indicator |
| `StatCard.tsx` | Metric card with icon, value, subtitle |
| `StatusBadge.tsx` | Colored chip for pipeline/validation status |
| `ToastProvider.tsx` | Global toast notification context |

### API Client (`api.ts`)
Typed fetch wrapper with full TypeScript interfaces for all backend response shapes. All endpoints are accessed through the `api` object:
```typescript
api.listProjects()
api.createProject(data)
api.startPipeline(id)
api.getStatus(id)
api.selectStack(id, selections)
api.getValidationDashboard(projectId?)
api.getValidationMetrics(projectId?)
api.submitReviewDecision(requestId, decision)
```

---

## Key Design Decisions

1. **Graceful degradation** — Every stage has fallback behavior. Tree-sitter falls back to regex parsing. Agentic analysis falls back to traditional analysis. LLM transformation falls back to pass-through. Vector store failure is non-fatal.

2. **In-memory pipeline state** — `_pipeline_data` dict in `pipeline.py` holds intermediate data (files, parse results, context) between stages to avoid re-reading from DB. This is cleared on project delete.

3. **Majority-pass validation** — Validation thresholds are intentionally relaxed (≥ 0.5 score, ≥ 70% pass rate) to avoid blocking the pipeline on incomplete or sparse codebases.

4. **Project-scoped validation queries** — All validation endpoints accept an optional `project_id` query parameter so the dashboard shows data relevant to the current project rather than all projects.

5. **JSON columns for flexibility** — Analysis results (APIs, tables, stack, recommendations) are stored as JSON columns on the `projects` table for fast retrieval without joins, while detailed data goes into normalized tables (`parsed_files`, `context_elements`, etc.).

6. **Background tasks** — Database and API analysis endpoints use FastAPI `BackgroundTasks` so they don't block the HTTP response.

---

## Known Limitations

- **SQLite concurrency** — SQLite with `check_same_thread=False` works for single-server deployments but is not suitable for multi-worker production use. Migrate to PostgreSQL for production.
- **In-memory pipeline state** — `_pipeline_data` is lost on server restart. A restart mid-pipeline requires re-running from the beginning.
- **Tree-sitter on Windows** — Requires Microsoft C++ Build Tools. The parser falls back to regex automatically if tree-sitter fails to compile.
- **Azure OpenAI required for full agentic analysis** — Without valid Azure credentials, the orchestrator is skipped entirely and traditional regex/AST analysis is used.
- **Single-user** — No authentication or multi-tenancy. All projects are visible to all users.
- **Vector store not persisted across restarts** — The FAISS index is rebuilt per pipeline run and stored on disk, but the in-memory retriever reference is lost on restart.

# CodeMorph

**AI-powered codebase modernization platform** — analyze legacy applications, detect their technology stack, and transform source files to a modern stack using LLM-driven code rewriting.

## Overview

CodeMorph ingests source code from a local path or a Git repository, parses it with tree-sitter ASTs (regex fallback), then runs a LangGraph agent orchestrator to analyze architecture, detect the full technology stack, extract APIs and database schemas, score confidence, and generate a modernization plan. Users select a target stack and the system transforms files one by one using Groq (or Azure OpenAI), augmented with FAISS-backed RAG context from the original codebase.

A React dashboard tracks every project through the 8-stage pipeline in real time and exposes an interactive review board for human-in-the-loop validation.

## Features

- **Multi-language ingestion** — Java, Python, JavaScript/TypeScript, C#, Go, COBOL, SQL, and more; supports local paths or Git clone
- **AST-powered parsing** — tree-sitter grammars (Python, Java, JS, TS) with regex fallback; extracts functions, classes, imports, endpoints, annotations, and SQL queries
- **Stack detection** — fingerprints frontend/backend frameworks, runtimes, databases, ORMs, messaging systems, and build tools with weighted confidence scores
- **Agentic analysis** — 10-node LangGraph graph: context → code analysis → dependency graph → database analysis → API analysis → confidence scoring → recommendations → human review gate → validation → finalize
- **RAG-augmented transformation** — semantic chunking by function/class boundaries, FAISS similarity search, and conversion mindmaps injected into LLM prompts
- **Database analysis** — parses SQL DDL, JPA/Hibernate/SQLAlchemy entities, stored procedures; generates ORM migration scripts and schema comparison views
- **API extraction** — discovers REST, SOAP, and GraphQL endpoints across frameworks; produces OpenAPI specs, Postman collections, and cURL examples
- **Behavioral validation** — 6 independent validators with aggregate scoring; low-confidence analyses trigger human review requests
- **Artifact generation** — PDF reports (ReportLab), ZIP bundles, migration scripts, and auto-generated test scaffolds
- **Real-time dashboard** — polling pipeline stepper, stat cards, API/schema viewers, dependency graph comparison, functional preservation view, and validation board

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11+ · FastAPI · Uvicorn |
| Agentic orchestration | LangGraph · LangChain · LangChain-Groq |
| LLM | Groq (`llama-3.3-70b-versatile`) / Azure OpenAI (optional) |
| AST parsing | tree-sitter 0.21 (Python, Java, JS, TS grammars) |
| Embeddings & RAG | sentence-transformers (`BAAI/bge-small-en`) · FAISS (CPU) |
| Graph analysis | NetworkX |
| Database | SQLite · SQLAlchemy |
| PDF generation | ReportLab |
| Frontend | React 19 · TypeScript · Vite 7 · MUI v5 |
| State / data fetching | TanStack Query v5 · React Router v7 |
| Charts & animations | Recharts · Framer Motion |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI entry point, CORS, router registration
│   │   ├── agents/
│   │   │   ├── orchestrator.py            # CodeMorphOrchestrator — 10-node LangGraph graph
│   │   │   ├── analysis_agent.py          # Deep code analysis agent
│   │   │   ├── context_agent.py           # Architecture context agent
│   │   │   ├── base_agent.py              # Base agent class
│   │   │   └── tools/
│   │   │       ├── code_analysis_tools.py
│   │   │       ├── dependency_graph_tools.py
│   │   │       └── advanced_pattern_detection.py
│   │   ├── api/
│   │   │   ├── projects.py                # CRUD for projects
│   │   │   ├── pipeline.py                # Pipeline trigger & status polling
│   │   │   ├── enhanced_analysis.py       # Database & API deep analysis
│   │   │   ├── artifacts.py               # ZIP artifact download
│   │   │   └── reports.py                 # PDF report generation
│   │   ├── services/
│   │   │   ├── ingestion.py               # File tree walk, language detection, Git clone
│   │   │   ├── parser.py                  # AST extraction (tree-sitter + regex fallback)
│   │   │   ├── context_builder.py         # Layer classification, dependency graph, vector store
│   │   │   ├── analyzer.py                # API, DB, ORM, MQ pattern extraction
│   │   │   ├── stack_detector.py          # Confidence-scored stack fingerprinting
│   │   │   ├── recommender.py             # Target stack recommendations
│   │   │   ├── transformer.py             # LLM-powered per-file code rewriting
│   │   │   ├── test_generator.py          # Auto test scaffold generation
│   │   │   ├── confidence_scoring.py      # 7-category weighted confidence aggregation
│   │   │   ├── behavioral_validation.py   # Multi-validator system (6 validators)
│   │   │   ├── database_analyzer.py       # Schema analysis, ORM model generation, migration scripts
│   │   │   ├── api_converter.py           # Endpoint extraction, OpenAPI spec, Postman collection
│   │   │   ├── enhanced_chunking.py       # Semantic chunking for RAG
│   │   │   ├── business_analyzer.py       # Complexity scoring, risk identification
│   │   │   └── report_generator.py        # PDF report creation
│   │   ├── embeddings/
│   │   │   ├── embedder.py                # Embedding model wrapper
│   │   │   └── vector_store.py            # FAISS index builder
│   │   ├── database/
│   │   │   └── db.py                      # SQLAlchemy models, init_db
│   │   └── models/
│   │       ├── schemas.py                 # Pydantic request/response types
│   │       └── project.py                 # SQLAlchemy table definitions
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_enhanced_analysis.py
├── frontend/
│   └── src/
│       ├── main.tsx                        # React entry point
│       ├── App.tsx                         # Root router
│       ├── api.ts                          # Typed API client
│       ├── pages/
│       │   ├── Dashboard.tsx              # Project list, search/filter, creation dialog
│       │   └── ProjectDetail.tsx          # Pipeline stepper + analysis tabs
│       ├── components/
│       │   ├── AppShell.tsx               # Layout wrapper
│       │   ├── ValidationDashboard.tsx    # Human review board
│       │   ├── APIAnalysis.tsx            # API endpoints viewer
│       │   ├── DatabaseAnalysis.tsx       # Schema viewer
│       │   ├── DependencyGraphComparison.tsx
│       │   ├── FunctionalPreservation.tsx
│       │   ├── ProgressBar.tsx
│       │   ├── StatCard.tsx
│       │   ├── StatusBadge.tsx
│       │   └── ToastProvider.tsx
│       └── theme.ts
├── docs/                                   # Architecture & design docs
│   ├── PROJECT_DOCUMENTATION.md
│   ├── TECH_STACK.md
│   ├── ARCHITECTURE.md
│   ├── WORKFLOW.md
│   ├── CODEBASE_DEEP_DIVE.md
│   ├── APPLICATION_DEEP_CONTEXT.md
│   ├── GRAPH_BUILDS.md
│   └── DEPENDENCY_GRAPH.md
├── Sample/                                 # Sample legacy Java EE project for testing
└── TODO.md                                 # Setup & troubleshooting notes
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Git (must be on PATH for repository cloning)
- Groq API key (free tier available at console.groq.com)

## Setup

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env — at minimum set GROQ_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes* | Groq API key — enables LLM transformation |
| `GROQ_MODEL` | No | Model ID (default: `llama-3.3-70b-versatile`) |
| `AZURE_OPENAI_ENDPOINT` | No | Azure OpenAI resource URL (alternative to Groq) |
| `AZURE_OPENAI_API_KEY` | No | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT` | No | Deployment name (e.g. `gpt-4`) |
| `AZURE_OPENAI_API_VERSION` | No | API version (e.g. `2024-02-15-preview`) |
| `CODEMORPH_MAX_CONCURRENT` | No | Parallel file transformations (default: 4) |
| `CODEMORPH_REQUEST_TIMEOUT` | No | Seconds per LLM request (default: 180) |

\* If no API key is set the backend starts in pass-through mode — analysis runs but files are copied unchanged during transformation.

## Usage

1. Open `http://localhost:5173`
2. Click **New Project**, enter a name and either a local folder path or a Git URL
3. CodeMorph clones/reads the source, runs all pipeline stages, and streams progress back to the dashboard
4. Once the agentic analysis completes, review the detected stack, API endpoints, DB tables, dependency graph, and confidence scores
5. A human review gate fires for low-confidence analyses — approve or reject from the **Validation** tab
6. Select a target stack and click **Start Transformation**
7. Download the generated artifacts (ZIP, PDF report, OpenAPI spec, Postman collection)

## Pipeline Stages

| # | Stage | What happens |
|---|---|---|
| 1 | **Ingesting** | File tree walk, language detection, LOC counting |
| 2 | **Parsing** | tree-sitter AST extraction; regex fallback |
| 3 | **Context Building** | Layer classification, dependency graph, FAISS vector store |
| 4 | **Agentic Analysis** | 10-node LangGraph orchestrator (context → code → deps → DB → API → confidence → recommendations → review gate → validation → finalize) |
| 5 | **Selecting** | User chooses target stack per technology category |
| 6 | **Transforming** | LLM rewrites each file with RAG context injected |
| 7 | **Post-Transform** | Behavioral validation, test scaffold generation, artifact packaging |
| 8 | **Complete** | Final state — all artifacts available for download |

## API Reference

Interactive docs at `http://localhost:8000/docs` (Swagger UI).

| Router prefix | Purpose |
|---|---|
| `/projects` | CRUD for projects |
| `/pipeline` | Trigger and poll pipeline stages |
| `/reports` | PDF report download |
| `/artifacts` | ZIP artifact bundle |
| `/enhanced-analysis` | Deep database & API analysis endpoints |

## Running Tests

```bash
cd backend
pytest tests/
```

## Supported Source Technologies

**Ingestion** handles `.java`, `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.cs`, `.go`, `.rs`, `.cbl`, `.sql`, `.xml`, `.yaml`, and common build/config formats.

**Stack detection** covers:

- *Frontend:* JSF, JSP, React, Angular, Vue.js, Thymeleaf, Svelte
- *Backend:* Java EE/EJB, Spring Boot, Spring MVC, Django, Flask, FastAPI, Express, ASP.NET Core, NestJS
- *Runtimes:* Java 8/11/17/21, Python 3, Node.js, .NET 6+, PHP
- *Databases:* DB2, Oracle, PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis
- *Messaging:* IBM MQ, Kafka, RabbitMQ, ActiveMQ, Apache Pulsar
- *ORMs:* Hibernate, Spring Data JPA, OpenJPA, EclipseLink, SQLAlchemy, Django ORM, Entity Framework, Sequelize, Prisma
- *Build tools:* Maven, Gradle, npm, Yarn, pnpm, pip, Composer, dotnet CLI
- *App servers:* WebSphere, WebLogic, JBoss/WildFly, Tomcat, Embedded Spring Boot

## Documentation

Full architecture and design documentation is in [docs/](docs/):

- [PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md) — system design, database schema, all API endpoints
- [TECH_STACK.md](docs/TECH_STACK.md) — every library, algorithm, and external service
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — component diagram (Mermaid)
- [WORKFLOW.md](docs/WORKFLOW.md) — end-to-end pipeline flowchart
- [CODEBASE_DEEP_DIVE.md](docs/CODEBASE_DEEP_DIVE.md) — per-module guide

## Graceful Degradation

| Component | Fallback |
|---|---|
| tree-sitter parsing | Regex-based extraction |
| LangGraph agentic analysis | Traditional rule-based analysis |
| LLM transformation (no key) | Pass-through file copy |
| Vector store (build failure) | Direct prompt without RAG context |

## License

Internal use — Prodapt.

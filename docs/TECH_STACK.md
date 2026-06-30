# CodeMorph — Tech Stack, Algorithms & Dependencies

---

## Architecture Overview

CodeMorph is a full-stack codebase modernisation platform with three distinct layers:
- **Frontend** — React SPA served by Vite
- **Backend** — Python async REST API (FastAPI)
- **AI / Agentic Layer** — LangGraph orchestrator calling Azure OpenAI

---

## Frontend

### Core Framework
| Library | Version | Purpose |
|---|---|---|
| React | 19.2 | UI component framework |
| React DOM | 19.2 | DOM rendering |
| TypeScript | 5.9 | Static typing |
| Vite | 7.3 | Build tool + dev server |

### UI & Styling
| Library | Version | Purpose |
|---|---|---|
| MUI (Material UI) | 5.18 | Component library — cards, tabs, steppers, chips |
| MUI Icons Material | 5.18 | Icon set |
| Emotion React / Styled | 11.14 | CSS-in-JS engine (MUI peer dep) |
| Framer Motion | 12.35 | Animated progress bars, transitions |
| Tailwind CSS | 4.2 | Utility CSS (supplementary) |
| tailwind-merge | 3.5 | Conditional class merging |
| clsx | 2.1 | Conditional className helper |
| Lucide React | 0.577 | Additional icon set |

### Data & Routing
| Library | Version | Purpose |
|---|---|---|
| TanStack Query (React Query) | 5.90 | Server state, caching, polling |
| React Router DOM | 7.13 | Client-side routing |
| Recharts | 3.8 | Charts (validation metrics) |

### Dev Tools
| Tool | Purpose |
|---|---|
| ESLint 9 + typescript-eslint | Linting |
| eslint-plugin-react-hooks | Hooks rules enforcement |
| @vitejs/plugin-react | Vite React transform |

---

## Backend

### Web Framework & Server
| Library | Purpose |
|---|---|
| **FastAPI** | Async REST API framework, OpenAPI auto-docs |
| **Uvicorn** (standard) | ASGI server with WebSocket + HTTP/2 support |
| **Pydantic** | Request/response validation and serialisation |
| **python-dotenv** | `.env` file loading |

### Database
| Library | Purpose |
|---|---|
| **SQLAlchemy** | ORM + query builder |
| **SQLite** | Embedded relational database (file: `data/codemorph.db`) |

### AI / LLM
| Library | Purpose |
|---|---|
| **openai** (AsyncAzureOpenAI) | Azure OpenAI client — async completions for code transformation |
| **langchain** | LLM abstraction, prompt templates, tool binding |
| **langchain-openai** | LangChain ↔ Azure OpenAI adapter |
| **langchain-community** | Community integrations |
| **langgraph** | Stateful agent graph orchestration (StateGraph, conditional edges) |

### Embeddings & Vector Search
| Library | Purpose |
|---|---|
| **sentence-transformers** | Local embedding model loader (HuggingFace) |
| **faiss-cpu** | FAISS IndexFlatIP — inner-product similarity search for RAG |
| **numpy** | Vector array operations |

### AST Parsing
| Library | Purpose |
|---|---|
| **tree-sitter** 0.21.3 | Core AST parser engine |
| **tree-sitter-python** 0.21 | Python grammar |
| **tree-sitter-java** 0.21 | Java grammar |
| **tree-sitter-javascript** 0.21 | JavaScript grammar |
| **tree-sitter-typescript** 0.21 | TypeScript grammar |

### Utilities
| Library | Purpose |
|---|---|
| **reportlab** | PDF generation (legacy analysis + migration reports) |
| **networkx** | Dependency graph construction and traversal |
| **sqlparse** | SQL statement parsing and formatting |
| **regex** | Extended regex engine (Unicode, recursive patterns) |
| **jinja2** | Template rendering |
| **jsonschema** | JSON schema validation |

### Testing
| Library | Purpose |
|---|---|
| **pytest** | Test runner |
| **pytest-asyncio** | Async test support |

---

## Algorithms & Techniques

### Code Parsing
| Algorithm / Technique | Where Used |
|---|---|
| **Tree-sitter incremental parsing** | Primary AST extraction for Python, Java, JS, TS — produces concrete syntax trees with line numbers |
| **Regex-based structural extraction** | Fallback for all languages; also used for framework-specific patterns (annotations, routes, SQL) that tree-sitter doesn't cover |
| **Language fingerprinting** | File extension + content heuristics to detect language and framework (Spring Boot, Django, Flask, React, Angular, etc.) |

### Embeddings & RAG
| Algorithm / Technique | Where Used |
|---|---|
| **BAAI/bge-small-en sentence embeddings** | 384-dimension dense vectors for code chunks |
| **Cosine similarity via FAISS IndexFlatIP** | Nearest-neighbour retrieval of relevant code context during LLM transformation |
| **Fixed-size + semantic chunking** | Files split by function/class boundaries first; falls back to 50–80 line windows |

### Agentic Orchestration
| Algorithm / Technique | Where Used |
|---|---|
| **LangGraph StateGraph** | Directed acyclic graph of pipeline nodes: initialize → context → code analysis → dependency → database → API → confidence → recommendations → human review → validation → finalize |
| **Conditional edge routing** | `_should_require_human_review` branches the graph to human review gate or directly to validation based on confidence threshold |
| **Tool-augmented LLM agents** | `AnalysisAgent` and `ContextAgent` bind tools (AST, complexity, dependency, pattern, security) to AzureChatOpenAI via LangChain tool calling |

### Confidence Scoring
| Algorithm / Technique | Where Used |
|---|---|
| **Weighted category aggregation** | 7 categories (parsing, analysis, pattern detection, architecture, security, dependencies, recommendations) each scored 0–1 and combined with fixed weights |
| **Score consistency modifier** | Standard deviation across category scores applies ±10% modifier to overall confidence |
| **McCabe cyclomatic complexity proxy** | `1 + (decision_keywords / LOC) * 100` — counts `if/elif/else/for/while/catch/except/and/or` per file |
| **Halstead-inspired maintainability index** | `max(0, min(100, 100 - (decisions/LOC * 50) - (avg_line_length / 10)))` — 0–100 scale |

### Validation
| Algorithm / Technique | Where Used |
|---|---|
| **Majority-pass rule** | ≥70% of 6 validators passing → Approved; 40–70% → Requires Review; <40% → Rejected |
| **Pass-through detection** | Regex scan of transformed file content for `# TODO.*transform`, `pass-through`, `original content` markers |
| **Approval rate formula** | `pass / (pass + warn + skipped)` — warn and skip dilute but don't contribute |
| **Passthrough ratio** | `(total_output_files - passthrough_count) / total_input_files` for transformation completeness score |

### Transformation
| Algorithm / Technique | Where Used |
|---|---|
| **LLM-powered file rewrite** | Each source file sent to Azure OpenAI with a migration mindmap prompt + RAG context; output is the fully rewritten target-stack file |
| **Catch-all mapping** | Files not covered by any detected stack category are grouped into a fallback mapping so 100% of files are always transformed |
| **Endpoint merge strategy** | Re-parsed transformed endpoints merged with original endpoints by `(method, path)` key — originals carried forward if not found in re-parse |
| **Stem-based path resolution** | Original file paths mapped to transformed paths by matching base filename stems (handles directory restructuring) |

### Dependency Analysis
| Algorithm / Technique | Where Used |
|---|---|
| **Import graph construction** | Language-specific import extraction builds a directed graph of module dependencies |
| **Circular dependency detection** | Bidirectional edge check in the import adjacency map |
| **Coupling score heuristic** | `min(1.0, len(imports) * 0.1 + inheritance_bonus)` — Low/Medium/High classification |

---

## External Services

| Service | Purpose |
|---|---|
| **Azure OpenAI** (gpt-4 / gpt-4o) | Code transformation (per-file rewrite) + agentic analysis (AnalysisAgent, ContextAgent) |
| **HuggingFace Hub** | Model download for `BAAI/bge-small-en` sentence transformer (runs locally after download) |

---

## Data Storage

| Store | Technology | Contents |
|---|---|---|
| Relational DB | SQLite via SQLAlchemy | Projects, pipeline runs, analysis results, parsed files, transformed files, context elements, validation results, review requests |
| Vector index | FAISS (disk-persisted) | Code chunk embeddings per project (`data/vector_stores/<project_id>/`) |
| In-memory state | Python dict (`_pipeline_data`) | Live pipeline intermediate data (files, parse results, context, transformed files) — cleared on server restart |
| Artifact ZIP | Temp filesystem | Transformed codebase ZIP for download |

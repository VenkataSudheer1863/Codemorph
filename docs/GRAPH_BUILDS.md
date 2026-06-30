# CodeMorph — Graph Builds: Visual Technical Reference

CodeMorph constructs **three distinct graphs** during its pipeline. Each is a genuine graph — a set of vertices (V) and directed edges (E) — but each serves a different purpose, uses different construction techniques, and is stored differently.

---

## Graph 1 — LangGraph Orchestration Graph

**What:** Directed control-flow graph of computation steps (not the codebase).
**Library:** `langgraph` — Pregel-style message-passing executor.
**Built once** at orchestrator init; executed per analysis run via `graph.ainvoke()`.

### Visual — Full Graph

```mermaid
flowchart TD
    START(["▶ START\nainvoke(initial_state)"])

    N1["🔷 initialize\n_initialize_state()\nValidate files · set start_time\nrecord languages"]
    N2["🔷 context_analysis\n_run_context_analysis()\nContextAgent: layer classify\ncross-cutting · import map"]
    N3["🔷 code_analysis\n_run_code_analysis()\nAnalysisAgent: AST · complexity\nsecurity · patterns"]
    N4["🔷 dependency_analysis\n_run_dependency_analysis()\nBuild file/class/function graph\ncalculate dep confidence"]
    N5["🔷 database_analyzer\n_run_database_analysis()\nDatabaseAnalyzer: schema\nORM model generation"]
    N6["🔷 api_analyzer\n_run_api_analysis()\nAPIConverter: endpoints\nOpenAPI spec"]
    N7["🔷 confidence_scoring\n_calculate_confidence_scores()\nConfidenceScoringEngine\n7 categories · weighted avg"]
    N8["🔷 generate_recommendations\n_generate_recommendations()\nArchitecture · Security\nPerformance · Modernisation"]

    COND{"🔀 _should_require_human_review()\noverall_confidence < 0.7 ?\nsecurity_confidence < 0.5 ?\nerrors present ?"}

    N9["🔶 human_review_gate\n_human_review_gate()\nCheck confidence threshold\nFlag for review if below"]
    N10["🔷 validation\n_validate_results()\nCompleteness · Consistency\nConfidence levels"]
    N11["🔷 finalize\n_finalize_results()\nAssemble final summary\nRecord execution time"]
    STOP(["⏹ END"])

    START --> N1
    N1 -->|"add_edge"| N2
    N2 -->|"add_edge"| N3
    N3 -->|"add_edge"| N4
    N4 -->|"add_edge"| N5
    N5 -->|"add_edge"| N6
    N6 -->|"add_edge"| N7
    N7 -->|"add_edge"| N8
    N8 --> COND
    COND -->|"'human_review'"| N9
    COND -->|"'validation'"| N10
    N9 -->|"add_edge"| N10
    N10 -->|"add_edge"| N11
    N11 -->|"add_edge"| STOP

    classDef node fill:#1e3a5f,color:#fff,stroke:#4a90d9,stroke-width:2px
    classDef cond fill:#3d2a00,color:#fff,stroke:#fbbf24,stroke-width:2px
    classDef gate fill:#3b1f00,color:#fff,stroke:#fb923c,stroke-width:2px
    classDef se fill:#1a1a2e,color:#fff,stroke:#818cf8,stroke-width:2px
    class N1,N2,N3,N4,N5,N6,N7,N8,N10,N11 node
    class COND cond
    class N9 gate
    class START,STOP se
```

### Visual — AgentState flowing through nodes

```mermaid
flowchart LR
    subgraph STATE["AgentState TypedDict — shared mutable state"]
        direction TB
        S1["input_data\n(files + project_context)"]
        S2["context_results\n← context_analysis"]
        S3["analysis_results\n← code_analysis"]
        S4["dependency_graph\n← dependency_analysis"]
        S5["database_analysis\n← database_analyzer"]
        S6["api_analysis\n← api_analyzer"]
        S7["confidence_scores\n← confidence_scoring"]
        S8["recommendations\n← generate_recommendations"]
        S9["validation_results\n← human_review_gate / validation"]
        S10["completed_steps\nerrors · current_step"]
    end

    N1["initialize"] -->|"writes context{}"| S1
    N2["context_analysis"] -->|"writes"| S2
    N3["code_analysis"] -->|"writes"| S3
    N4["dependency_analysis"] -->|"writes"| S4
    N5["database_analyzer"] -->|"writes"| S5
    N6["api_analyzer"] -->|"writes"| S6
    N7["confidence_scoring"] -->|"writes"| S7
    N8["generate_recommendations"] -->|"writes"| S8
    N9["validation"] -->|"writes"| S9
```

### Visual — Adjacency representation

```mermaid
graph LR
    I["initialize"] --> CA["context_analysis"]
    CA --> COA["code_analysis"]
    COA --> DA["dependency_analysis"]
    DA --> DBA["database_analyzer"]
    DBA --> AA["api_analyzer"]
    AA --> CS["confidence_scoring"]
    CS --> GR["generate_recommendations"]
    GR -->|"confidence OK"| V["validation"]
    GR -->|"confidence LOW"| HRG["human_review_gate"]
    HRG --> V
    V --> F["finalize"]
    F --> END(["END"])

    style GR fill:#3d2a00,color:#fff,stroke:#fbbf24
    style HRG fill:#3b1f00,color:#fff,stroke:#fb923c
```

---

## Graph 2 — Enhanced Dependency Graph

**What:** Directed, weighted, multi-type property graph of the codebase itself.
**Library:** Pure Python — `collections.defaultdict`, custom `@dataclass` objects, plain `dict`/`list`.
**Built** inside the `dependency_analysis` node of Graph 1.

### Visual — Node types and edge types

```mermaid
graph TD
    subgraph FILE_NODES["📄 File Nodes  (id: file:path)"]
        F1["file:src/UserService.java\ntype=file · lang=Java\nsize=2400 · lines=80"]
        F2["file:src/UserRepository.java\ntype=file · lang=Java\nsize=1200 · lines=40"]
        F3["file:src/OrderService.java\ntype=file · lang=Java\nsize=3100 · lines=95"]
    end

    subgraph CLASS_NODES["🟦 Class Nodes  (id: class:path:name)"]
        C1["class:…:UserService\ntype=class\nmethods=5"]
        C2["class:…:UserRepository\ntype=class\nmethods=3"]
        C3["class:…:OrderService\ntype=class\nmethods=7"]
        C4["class:…:BaseService\ntype=class\nmethods=2"]
    end

    subgraph FUNC_NODES["🟩 Function Nodes  (id: function:path:name)"]
        FN1["function:…:getUser\ntype=function\nparams=1"]
        FN2["function:…:saveUser\ntype=function\nparams=1"]
        FN3["function:…:createOrder\ntype=function\nparams=2"]
    end

    F1 -->|"contains  w=1.0"| C1
    F1 -->|"contains  w=1.0"| FN1
    F1 -->|"contains  w=1.0"| FN2
    F2 -->|"contains  w=1.0"| C2
    F3 -->|"contains  w=1.0"| C3
    F3 -->|"contains  w=1.0"| FN3

    F1 -->|"import  w=0.5"| F2
    F3 -->|"import  w=0.5"| F1

    FN3 -->|"call  w=1.0"| FN1
    FN3 -->|"call  w=1.0"| FN2

    C1 -->|"inheritance  w=2.0"| C4
    C3 -->|"inheritance  w=2.0"| C4

    classDef file fill:#1e3a5f,color:#fff,stroke:#4a90d9
    classDef cls fill:#1a4731,color:#fff,stroke:#4ade80
    classDef fn fill:#3b1f5e,color:#fff,stroke:#a78bfa
    class F1,F2,F3 file
    class C1,C2,C3,C4 cls
    class FN1,FN2,FN3 fn
```

### Visual — Edge weight legend

```mermaid
graph LR
    A["File A"] -->|"import  ──── w=0.5\n(loosest)"| B["File B"]
    C["File C"] -->|"contains  ── w=1.0"| D["Class D"]
    E["fn:getUser"] -->|"call  ──── w=1.0"| F["fn:saveUser"]
    G["Class G"] -->|"inheritance  w=2.0\n(tightest)"| H["Class H"]

    style A fill:#1e3a5f,color:#fff
    style B fill:#1e3a5f,color:#fff
    style C fill:#1e3a5f,color:#fff
    style D fill:#1a4731,color:#fff
    style E fill:#3b1f5e,color:#fff
    style F fill:#3b1f5e,color:#fff
    style G fill:#1a4731,color:#fff
    style H fill:#1a4731,color:#fff
```

### Visual — Cycle Detection Algorithm (DFS + recursion stack)

```mermaid
flowchart TD
    CD_START(["Start: for each node not in visited"])
    CD1["Push node to visited\nPush node to rec_stack\nAppend node to path"]
    CD2{"node already\nin rec_stack?"}
    CD3["🔴 CYCLE FOUND\nslice path from cycle_start\nappend to cycles list\nclassify type"]
    CD4{"node already\nin visited?"}
    CD5["return — already explored"]
    CD6["for each neighbor\nin graph\[node\]"]
    CD7["dfs(neighbor, path copy)"]
    CD8["Remove node from rec_stack\n(backtrack)"]
    CD_END(["All nodes processed\nReturn cycles list"])

    CD_START --> CD2
    CD2 -->|"Yes"| CD3
    CD2 -->|"No"| CD4
    CD4 -->|"Yes"| CD5
    CD4 -->|"No"| CD1
    CD1 --> CD6
    CD6 --> CD7
    CD7 --> CD6
    CD6 -->|"done"| CD8
    CD8 --> CD_END

    style CD3 fill:#7f1d1d,color:#fff,stroke:#ef4444
```

### Visual — Example cycle detected

```mermaid
graph LR
    A["file:OrderService"] -->|"import"| B["file:UserService"]
    B -->|"import"| C["file:PaymentService"]
    C -->|"import"| A

    style A fill:#7f1d1d,color:#fff,stroke:#ef4444
    style B fill:#7f1d1d,color:#fff,stroke:#ef4444
    style C fill:#7f1d1d,color:#fff,stroke:#ef4444
```

> Cycle path: `[OrderService → UserService → PaymentService → OrderService]`
> Type: `file_cycle` · Length: 3

### Visual — Cluster Detection (undirected flood-fill)

```mermaid
flowchart TD
    CL1["Make graph undirected:\nadd both A→B and B→A\nfor every edge"]
    CL2["for each node not in visited"]
    CL3["DFS flood-fill\nfrom this node"]
    CL4["Collect all reachable\nnodes into cluster[]"]
    CL5{"cluster size > 1?"}
    CL6["Compute cohesion:\ninternal_edges /\nn*(n-1)"]
    CL7["Append to clusters list"]
    CL8["Sort by size DESC"]

    CL1 --> CL2 --> CL3 --> CL4 --> CL5
    CL5 -->|"Yes"| CL6 --> CL7 --> CL8
    CL5 -->|"No"| CL2
```

### Visual — Example clusters

```mermaid
graph TD
    subgraph CLUSTER_A["Cluster A  size=4  cohesion=0.67"]
        A1["UserService"] --- A2["UserRepository"]
        A2 --- A3["UserModel"]
        A1 --- A3
        A3 --- A4["BaseEntity"]
    end

    subgraph CLUSTER_B["Cluster B  size=3  cohesion=0.33"]
        B1["OrderService"] --- B2["OrderRepository"]
        B2 --- B3["OrderModel"]
    end

    subgraph ISOLATED["Isolated  size=1"]
        X["ConfigLoader"]
    end
```

### Visual — Hotspot Identification

```mermaid
flowchart LR
    HS1["Count in_degree\nand out_degree\nfor every node\nO(E)"]
    HS2["score = (in_degree×2 + out_degree) / 3\nfor every node\nO(V)"]
    HS3{"score > 2?"}
    HS4["Add to hotspots\nAssign risk level"]
    HS5["Sort by score DESC"]

    HS1 --> HS2 --> HS3
    HS3 -->|"Yes"| HS4 --> HS5
    HS3 -->|"No"| HS2
```

### Visual — Example hotspot graph

```mermaid
graph TD
    CORE["⚠️ UserService\nin_degree=6  out_degree=2\nscore=4.67  risk=HIGH"]

    S1["OrderService"] -->|"import"| CORE
    S2["PaymentService"] -->|"import"| CORE
    S3["AuthService"] -->|"import"| CORE
    S4["NotificationService"] -->|"import"| CORE
    S5["ReportService"] -->|"import"| CORE
    S6["AdminService"] -->|"import"| CORE
    CORE -->|"import"| DB1["UserRepository"]
    CORE -->|"import"| DB2["UserModel"]

    style CORE fill:#7f1d1d,color:#fff,stroke:#ef4444,stroke-width:3px
```

### Visual — Architectural Violation Detection

```mermaid
flowchart TD
    AV1["Classify each node's\nfile path into a layer\nby keyword scan"]
    AV2["Layer hierarchy:\n0=presentation\n1=business\n2=data\n3=infrastructure"]
    AV3["For each edge:\nget source_level\nget target_level"]
    AV4{"source_level >\ntarget_level + 1?"}
    AV5["🔴 VIOLATION\nRecord source/target layers\nseverity = high if gap > 2\nelse medium"]
    AV6["✅ OK — valid\nlayer dependency"]

    AV1 --> AV2 --> AV3 --> AV4
    AV4 -->|"Yes — skips a layer"| AV5
    AV4 -->|"No"| AV6

    style AV5 fill:#7f1d1d,color:#fff,stroke:#ef4444
    style AV6 fill:#1a4731,color:#fff,stroke:#4ade80
```

### Visual — Example valid vs violated dependencies

```mermaid
graph TD
    subgraph VALID["✅ Valid Layer Dependencies"]
        V_P["Presentation\nOrderController"] -->|"OK"| V_B["Business\nOrderService"]
        V_B -->|"OK"| V_D["Data\nOrderRepository"]
        V_D -->|"OK"| V_I["Infrastructure\nDatabaseConfig"]
    end

    subgraph VIOLATED["🔴 Architectural Violations"]
        X_P["Presentation\nOrderController"] -->|"VIOLATION\nskips Business"| X_D["Data\nOrderRepository"]
        X_B["Business\nOrderService"] -->|"VIOLATION\nskips 2 layers"| X_I["Infrastructure\nDatabaseConfig"]
    end

    style X_P fill:#7f1d1d,color:#fff
    style X_D fill:#7f1d1d,color:#fff
    style X_B fill:#7f1d1d,color:#fff
    style X_I fill:#7f1d1d,color:#fff
```

### Visual — Complete Graph 2 data structure

```mermaid
graph TD
    subgraph GRAPH2["Graph 2 Output Dict"]
        direction TB
        G_NODES["nodes: Dict\[str, dict\]\nkey = namespaced ID\nvalue = node.__dict__"]
        G_EDGES["edges: List\[dict\]\neach = DependencyEdge.__dict__\n{source, target, type, weight, metadata}"]
        G_NC["node_count: int"]
        G_EC["edge_count: int"]
    end

    subgraph ANALYSIS["analysis: Dict"]
        direction TB
        A_M["metrics:\ndensity · avg_degree\nmax_degree · complexity_score"]
        A_C["cycles:\n\[{cycle\[\], length, type}\]"]
        A_CL["clusters:\n\[{nodes\[\], size, cohesion}\]"]
        A_CP["critical_paths:\n\[{path\[\], length, impact_score}\]"]
        A_H["hotspots:\n\[{node, score, risk_level}\]"]
        A_V["architectural_violations:\n\[{source, target, severity}\]"]
    end

    GRAPH2 --> ANALYSIS
```

---

## Graph 3 — Context Builder Layer Graph

**What:** Directed layer-classification graph mapping files to architecture layers and classes to imports.
**Library:** Pure Python — `collections.defaultdict` only.
**Built** in Stage 3 (before agentic analysis), feeds transformer, validators, and audit report.

### Visual — Layer classification decision tree

```mermaid
flowchart TD
    INPUT["File: path + extension\n+ framework_patterns"]

    P1{"Any path segment\nmatches LAYER_KEYWORDS\n\[layer\]\[paths\]?"}
    P2{"Extension matches\nLAYER_KEYWORDS\n\[layer\]\[extensions\]?"}
    P3{"Detected framework\nmatches LAYER_KEYWORDS\n\[layer\]\[frameworks\]?"}
    DEFAULT["→ backend\n(default)"]

    L_FE["→ frontend\npaths: frontend/client/web/ui\nexts: .html .jsx .tsx .css\nfw: React Angular Vue JSF"]
    L_BE["→ backend\npaths: backend/server/api/service\nexts: .java .py .cs .go\nfw: Spring Boot FastAPI Django"]
    L_DB["→ database\npaths: db/dao/repository/entity\nexts: .sql .ddl\nfw: Hibernate JPA"]
    L_INT["→ integration\npaths: integration/gateway/queue\nfw: SOAP/JAX-WS"]
    L_DEP["→ deployment\npaths: k8s/docker/terraform\nexts: .yaml .yml"]

    INPUT --> P1
    P1 -->|"Yes"| L_FE
    P1 -->|"Yes"| L_BE
    P1 -->|"Yes"| L_DB
    P1 -->|"Yes"| L_INT
    P1 -->|"Yes"| L_DEP
    P1 -->|"No"| P2
    P2 -->|"Yes"| L_FE
    P2 -->|"Yes"| L_BE
    P2 -->|"Yes"| L_DB
    P2 -->|"No"| P3
    P3 -->|"Yes"| L_FE
    P3 -->|"Yes"| L_BE
    P3 -->|"Yes"| L_DB
    P3 -->|"No"| DEFAULT
```

### Visual — Full layer graph with nodes and edges

```mermaid
graph TD
    subgraph LAYERS["5 Layer Nodes (fixed vertices)"]
        FE["🖥 frontend\nfiles\[\] · components\[\]\nframeworks\[\] · file_count"]
        BE["⚙️ backend\nfiles\[\] · components\[\]\nframeworks\[\] · file_count"]
        DB["🗄 database\nfiles\[\] · components\[\]\nframeworks\[\] · file_count"]
        INT["🔌 integration\nfiles\[\] · components\[\]\nframeworks\[\] · file_count"]
        DEP["🚀 deployment\nfiles\[\] · components\[\]\nframeworks\[\] · file_count"]
    end

    subgraph FILES["Source Files (classified)"]
        F1["OrderController.java\n(path: controller/)"]
        F2["UserService.java\n(path: service/)"]
        F3["UserRepository.java\n(path: repository/)"]
        F4["schema.sql\n(ext: .sql)"]
        F5["App.tsx\n(ext: .tsx)"]
        F6["docker-compose.yml\n(ext: .yml)"]
    end

    subgraph CLASSES["Class/Component Nodes"]
        CL1["OrderController\nlayer=backend"]
        CL2["UserService\nlayer=backend"]
        CL3["UserRepository\nlayer=database"]
    end

    subgraph IMPORTS["Import Dependencies\n(defaultdict edges)"]
        IMP1["java.util.List\norg.springframework.web"]
        IMP2["java.util.Optional\norg.springframework.stereotype"]
    end

    F1 -->|"classified to"| BE
    F2 -->|"classified to"| BE
    F3 -->|"classified to"| DB
    F4 -->|"classified to"| DB
    F5 -->|"classified to"| FE
    F6 -->|"classified to"| DEP

    F1 -->|"contains"| CL1
    F2 -->|"contains"| CL2
    F3 -->|"contains"| CL3

    CL1 -->|"depends on\n(all imports in file)"| IMP1
    CL2 -->|"depends on\n(all imports in file)"| IMP2

    classDef layer fill:#1e3a5f,color:#fff,stroke:#4a90d9
    classDef file fill:#1a4731,color:#fff,stroke:#4ade80
    classDef cls fill:#3b1f5e,color:#fff,stroke:#a78bfa
    classDef imp fill:#1f2937,color:#fff,stroke:#6b7280
    class FE,BE,DB,INT,DEP layer
    class F1,F2,F3,F4,F5,F6 file
    class CL1,CL2,CL3 cls
    class IMP1,IMP2 imp
```

### Visual — Graph 3 final data structure

```mermaid
graph TD
    subgraph G3["Graph 3 Output Dict"]
        direction TB
        G3_L["layers: Dict\[str, Dict\]\n5 fixed keys\neach: {files\[\], components\[\], frameworks\[\], file_count}"]
        G3_C["components: List\[Dict\]\n{name, type, file, layer, language}\none per class across all files"]
        G3_D["dependencies: Dict\[str, List\]\ndefaultdict(set) → serialised\nclass_name → \[import_strings\]"]
        G3_SM["service_map: Dict\[str, List\]\nclass_name → \[file_paths\]"]
        G3_TC["total_components: int"]
        G3_PS["project_summary: str\n(from BusinessAnalyzer)"]
    end
```

---

## Side-by-side visual comparison

```mermaid
graph TD
    subgraph G1_BOX["Graph 1 — Orchestration\nLangGraph StateGraph\nPregl executor"]
        G1_V["V = 11 async functions"]
        G1_E["E = 9 unconditional\n+ 1 conditional (2 branches)"]
        G1_S["Storage: LangGraph\ninternal adjacency map"]
        G1_T["Traversal: Pregel\nmessage-passing"]
    end

    subgraph G2_BOX["Graph 2 — Dependency\nPure Python\ndict + list"]
        G2_V["V = files ∪ classes ∪ functions"]
        G2_E["E = contains · import\ncall · inheritance\nweights: 0.5 – 2.0"]
        G2_S["Storage: dict of nodes\n+ list of edges"]
        G2_T["Traversal: DFS cycles\nflood-fill clusters\ndegree centrality hotspots"]
    end

    subgraph G3_BOX["Graph 3 — Layer Map\nPure Python\ndefaultdict"]
        G3_V["V = 5 layers ∪ N classes"]
        G3_E["E = file→layer\nclass→import"]
        G3_S["Storage: defaultdict\n+ list"]
        G3_T["Traversal: implicit\n(dict lookups)"]
    end

    PIPE["Pipeline\nStage 3 → Stage 4"] --> G3_BOX
    PIPE --> G1_BOX
    G1_BOX -->|"node 3 triggers"| G2_BOX
```

---

## Why all three are real graphs — G = (V, E)

```mermaid
graph LR
    subgraph PROOF["Formal proof: G = (V, E)"]
        direction TB
        P1["Graph 1\nV = {initialize, context_analysis,\ncode_analysis, dependency_analysis,\ndatabase_analyzer, api_analyzer,\nconfidence_scoring, generate_recommendations,\nhuman_review_gate, validation, finalize}\n|V| = 11\nE = 9 unconditional + 1 conditional\n|E| = 10–11 depending on branch\nDirected ✓  Compiled ✓  Traversed ✓"]
        P2["Graph 2\nV = file_nodes ∪ class_nodes ∪ function_nodes\n|V| = O(files + classes + functions)\nE = contains ∪ import ∪ call ∪ inheritance\n|E| = O(V²) worst case\nDirected ✓  Weighted ✓  Analysed ✓"]
        P3["Graph 3\nV = {frontend, backend, database,\nintegration, deployment} ∪ class_nodes\n|V| = 5 + N classes\nE = file→layer ∪ class→import\nDirected ✓  Stored ✓  Queried ✓"]
    end
```

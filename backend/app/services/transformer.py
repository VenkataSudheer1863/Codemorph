"""Transformer Service.

LLM-powered code transformation engine using Groq with RAG context.
Rewrites source files from legacy to target stack while preserving business logic.
Falls back to pass-through mode if Groq is unavailable.
"""

import os
import re
import json
import asyncio
import logging
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Callable

from groq import AsyncGroq, APIConnectionError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

# ── Concurrency & timeout settings ────────────────────────────────────────────
# Max files transformed in parallel. Higher = faster but more API pressure.
_MAX_CONCURRENT = int(os.environ.get("CODEMORPH_MAX_CONCURRENT", "4"))
# Per-request timeout in seconds. Groq can be slow on large files.
_REQUEST_TIMEOUT = float(os.environ.get("CODEMORPH_REQUEST_TIMEOUT", "180.0"))
# On timeout, retry once with this reduced chunk size (chars)
_RETRY_CHUNK_CHARS = int(os.environ.get("CODEMORPH_RETRY_CHUNK", "8000"))


def _is_groq_configured() -> bool:
    """Check if Groq credentials are present."""
    return bool(os.environ.get("GROQ_API_KEY"))


def get_async_openai_client() -> Optional[AsyncGroq]:
    """Create an AsyncGroq client, or None if not configured."""
    if not _is_groq_configured():
        logger.warning("Groq is not configured — transformation will use pass-through mode")
        return None

    return AsyncGroq(
        api_key=os.environ["GROQ_API_KEY"],
        timeout=_REQUEST_TIMEOUT,
        max_retries=3,
    )


def build_transformation_mappings(
    detected_stack: list[dict],
    selected_stack: dict,
    analysis: dict,
    context: dict,
    files: list[dict],
) -> list[dict]:
    """Build a list of transformation tasks (mappings) from legacy to target.

    Returns list of mappings:
      - source: str (e.g. "EJB Services")
      - target: str (e.g. "Spring Boot Services")
      - file_count: int
      - files: list of file paths
      - status: str ("pending")
      - category: str
    """
    mappings = []
    layer_files = context.get("layers", {})

    # Map detected stack to component groups
    component_groups = _categorize_files_by_component(files, analysis, context)

    # Track which files are covered by a mapping
    covered_files: set = set()

    for item in detected_stack:
        category = item["category"]
        detected = item["detected"]
        target = selected_stack.get(category, "")

        if not target:
            continue

        # Find relevant files for this transformation
        relevant_files = component_groups.get(category, [])

        if relevant_files:
            source_label = _make_label(detected, category)
            target_label = _make_label(target, category)

            mappings.append({
                "source": source_label,
                "target": target_label,
                "file_count": len(relevant_files),
                "files": relevant_files,
                "status": "pending",
                "category": category,
            })
            covered_files.update(relevant_files)

    # Collect all file paths
    all_file_paths = [f["path"] for f in files]

    # If no specific mappings, create generic ones based on layers
    if not mappings:
        for layer_name, layer_data in layer_files.items():
            layer_file_list = layer_data.get("files", [])
            if layer_file_list:
                mappings.append({
                    "source": f"Legacy {layer_name.capitalize()}",
                    "target": f"Modern {layer_name.capitalize()}",
                    "file_count": len(layer_file_list),
                    "files": layer_file_list,
                    "status": "pending",
                    "category": layer_name,
                })
                covered_files.update(layer_file_list)

    # Ensure every file is covered — add a catch-all mapping for any uncovered files
    uncovered = [fp for fp in all_file_paths if fp not in covered_files]
    if uncovered:
        # Determine a sensible target label from the selected stack
        default_target = (
            selected_stack.get("backend_framework")
            or selected_stack.get("runtime")
            or next(iter(selected_stack.values()), "Modern Stack")
        )
        mappings.append({
            "source": "Legacy Files",
            "target": f"{default_target} (Migrated)",
            "file_count": len(uncovered),
            "files": uncovered,
            "status": "pending",
            "category": "general",
        })
        logger.info(f"Added catch-all mapping for {len(uncovered)} uncovered files")

    return mappings


def _categorize_files_by_component(
    files: list[dict],
    analysis: dict,
    context: dict,
) -> dict[str, list[str]]:
    """Categorize files into component groups matching stack categories."""
    groups: dict[str, list[str]] = {
        "frontend_framework": [],
        "backend_framework": [],
        "database": [],
        "orm": [],
        "messaging": [],
        "runtime": [],
        "build_tool": [],
        "app_server": [],
    }

    layers = context.get("layers", {})
    
    # Track which files have been categorized
    categorized_files = set()

    # Frontend files
    frontend_files = layers.get("frontend", {}).get("files", [])
    groups["frontend_framework"] = frontend_files
    categorized_files.update(frontend_files)

    # Backend files
    backend_files = layers.get("backend", {}).get("files", [])
    groups["backend_framework"] = backend_files
    groups["runtime"] = backend_files  # Runtime maps to same files
    categorized_files.update(backend_files)

    # Database files
    db_files = layers.get("database", {}).get("files", [])
    groups["database"] = db_files
    groups["orm"] = db_files
    categorized_files.update(db_files)

    # Integration files
    integration_files = layers.get("integration", {}).get("files", [])
    groups["messaging"] = integration_files
    categorized_files.update(integration_files)

    # Build/deploy files
    deploy_files = layers.get("deployment", {}).get("files", [])
    groups["app_server"] = deploy_files
    categorized_files.update(deploy_files)

    # Build tool files
    build_files = [
        f["path"] for f in files
        if f.get("filename") in {
            "pom.xml", "build.gradle", "build.gradle.kts",
            "package.json", "requirements.txt", "pyproject.toml",
        }
    ]
    groups["build_tool"] = build_files
    categorized_files.update(build_files)
    
    # Add any uncategorized files to the most appropriate group
    # This ensures ALL files are transformed
    all_file_paths = [f["path"] for f in files]
    uncategorized = [fp for fp in all_file_paths if fp not in categorized_files]
    
    if uncategorized:
        # Add uncategorized files to backend_framework as default
        # This ensures they get transformed
        groups["backend_framework"].extend(uncategorized)

    return groups


def _make_label(tech: str, category: str) -> str:
    """Create a readable label for a transformation mapping."""
    labels = {
        "frontend_framework": f"{tech} Components",
        "backend_framework": f"{tech} Services",
        "database": f"{tech} Database",
        "orm": f"{tech} Data Layer",
        "messaging": f"{tech} Messaging",
        "runtime": f"{tech} Runtime",
        "build_tool": f"{tech} Build Config",
        "app_server": f"{tech} Deployment",
    }
    return labels.get(category, tech)


async def transform_codebase(
    mappings: list[dict],
    files: list[dict],
    selected_stack: dict,
    context: dict,
    analysis: dict,
    rag_retriever=None,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """Transform the codebase using Azure OpenAI.

    Falls back to pass-through mode (preserving original files with TODO comments)
    if Azure OpenAI is not configured or unreachable.
    """
    client = get_async_openai_client()
    deployment = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    use_ai = client is not None

    # Quick connectivity check — try one test call
    if use_ai:
        try:
            # Use max_completion_tokens for newer API versions
            test_params = {
                "model": deployment,
                "messages": [{"role": "user", "content": "ping"}],
            }
            
            # Try with max_completion_tokens first (newer API)
            try:
                test_params["max_completion_tokens"] = 5
                await client.chat.completions.create(**test_params)
            except Exception as e:
                # Fallback to max_tokens for older API versions
                if "max_completion_tokens" in str(e):
                    test_params.pop("max_completion_tokens", None)
                    test_params["max_tokens"] = 5
                    await client.chat.completions.create(**test_params)
                else:
                    raise
            
            logger.info("Azure OpenAI connection verified")
        except Exception as e:
            logger.warning(f"Azure OpenAI connection test failed ({e}), switching to pass-through mode")
            use_ai = False
            await client.close()
            client = None

    transformed_files = {}
    total_files = sum(m["file_count"] for m in mappings)
    processed = 0
    errors = 0

    # Build a flat list of (file_path, mapping) work items preserving mapping order
    work_items: list[tuple[str, dict]] = []
    for mapping in mappings:
        for fp in mapping.get("files", []):
            work_items.append((fp, mapping))

    # Semaphore limits concurrent LLM calls to avoid overwhelming the API
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    async def _process_one(file_path: str, mapping: dict) -> tuple[str, str, bool]:
        """Transform a single file and return (new_path, content, had_error)."""
        file_content = _get_file_content(file_path, files)
        if not file_content:
            return _compute_new_path(file_path, mapping, selected_stack), "", False

        rag_context = ""
        if rag_retriever:
            try:
                rag_context = rag_retriever(file_content[:1000])
            except Exception:
                pass

        new_path = _compute_new_path(file_path, mapping, selected_stack)
        target_tech = mapping.get("target", "")

        if not use_ai:
            return new_path, _passthrough_transform(file_path, file_content, mapping["source"], target_tech), False

        async with semaphore:
            try:
                content = await _transform_file(
                    client=client,
                    deployment=deployment,
                    file_path=file_path,
                    content=file_content,
                    source=mapping["source"],
                    target=target_tech,
                    context_info=_build_transform_context(selected_stack, context, analysis, rag_context),
                )
                return new_path, content, False
            except (APITimeoutError, asyncio.TimeoutError) as e:
                # On timeout: retry once with a smaller chunk to guarantee a response
                logger.warning(
                    f"Timeout on {file_path} ({len(file_content)} chars) — "
                    f"retrying with reduced chunk ({_RETRY_CHUNK_CHARS} chars)"
                )
                try:
                    content = await _transform_file(
                        client=client,
                        deployment=deployment,
                        file_path=file_path,
                        content=file_content[:_RETRY_CHUNK_CHARS],
                        source=mapping["source"],
                        target=target_tech,
                        context_info=_build_transform_context(selected_stack, context, analysis, rag_context),
                        force_single_chunk=True,
                    )
                    # Append the untransformed remainder with a clear marker
                    if len(file_content) > _RETRY_CHUNK_CHARS:
                        remainder = file_content[_RETRY_CHUNK_CHARS:]
                        ext = Path(file_path).suffix
                        cmt = "#" if ext in (".py", ".rb", ".sh", ".yml", ".yaml") else "//"
                        content += (
                            f"\n\n{cmt} ===== CodeMorph: remainder of file (timeout on full transform) =====\n"
                            + remainder
                        )
                    logger.info(f"Retry succeeded for {file_path}")
                    return new_path, content, False
                except Exception as retry_err:
                    logger.error(f"Retry also failed for {file_path}: {retry_err}")
                    return new_path, _passthrough_transform(file_path, file_content, mapping["source"], target_tech, str(retry_err)), True
            except RateLimitError as e:
                # Back off and retry once for rate limit
                wait = 30
                logger.warning(f"Rate limit on {file_path}, waiting {wait}s then retrying")
                await asyncio.sleep(wait)
                try:
                    async with semaphore:
                        content = await _transform_file(
                            client=client, deployment=deployment,
                            file_path=file_path, content=file_content,
                            source=mapping["source"], target=target_tech,
                            context_info=_build_transform_context(selected_stack, context, analysis, rag_context),
                        )
                    return new_path, content, False
                except Exception as retry_err:
                    logger.error(f"Rate limit retry failed for {file_path}: {retry_err}")
                    return new_path, _passthrough_transform(file_path, file_content, mapping["source"], target_tech, str(retry_err)), True
            except Exception as e:
                logger.error(f"Error transforming {file_path}: {e}")
                return new_path, _passthrough_transform(file_path, file_content, mapping["source"], target_tech, str(e)), True

    # Mark all mappings active upfront
    for mapping in mappings:
        mapping["status"] = "active"
    if progress_callback:
        await progress_callback(mappings, 0, total_files)

    # Run all files concurrently (bounded by semaphore)
    tasks = [_process_one(fp, m) for fp, m in work_items]
    for coro in asyncio.as_completed(tasks):
        new_path, content, had_error = await coro
        if content:
            transformed_files[new_path] = content
        if had_error:
            errors += 1
        processed += 1
        if progress_callback and processed % max(1, _MAX_CONCURRENT) == 0:
            await progress_callback(mappings, processed, total_files)

    # Mark all mappings completed
    for mapping in mappings:
        mapping["status"] = "completed"

    if progress_callback:
        await progress_callback(mappings, total_files, total_files)

    # Close the async client
    if client:
        await client.close()

    mode = "AI-powered" if use_ai else "pass-through"
    logger.info(f"Transformation complete ({mode}): {len(transformed_files)} files, {errors} errors")

    return {
        "files": transformed_files,
        "total_transformed": len(transformed_files),
        "mode": mode,
        "errors": errors,
    }


def _passthrough_transform(
    file_path: str,
    content: str,
    source: str,
    target: str,
    error: str = "",
) -> str:
    """Generate a pass-through transformation with migration TODOs."""
    ext = Path(file_path).suffix
    comment_prefix = "#" if ext in (".py", ".rb", ".yml", ".yaml", ".toml", ".sh") else "//"
    if ext in (".html", ".xml", ".svg"):
        header = f"<!-- TODO [CodeMorph]: Migrate from {source} to {target} -->\n"
        if error:
            header += f"<!-- Migration error: {error} -->\n"
        return header + content

    header_lines = [
        f"{comment_prefix} ===== CodeMorph Migration TODO =====",
        f"{comment_prefix} Source: {source}",
        f"{comment_prefix} Target: {target}",
        f"{comment_prefix} File: {file_path}",
    ]
    if error:
        header_lines.append(f"{comment_prefix} Error: {error}")
    header_lines.append(f"{comment_prefix} TODO: Review and complete the migration for this file")
    header_lines.append(f"{comment_prefix} ====================================")
    header_lines.append("")

    return "\n".join(header_lines) + content


def _get_file_content(file_path: str, files: list[dict]) -> str:
    """Get file content from file list."""
    for f in files:
        if f.get("path") == file_path:
            return f.get("content", "")
    return ""


def _get_conversion_mindmap(selected_stack: dict) -> str:
    """Return a base conversion mindmap/blueprint that guides the LLM before any file is transformed.
    This gives the model a holistic picture of the migration so individual file transforms
    are consistent with the overall architecture plan.
    """
    frontend = selected_stack.get("frontend_framework", "React")
    backend = selected_stack.get("backend_framework", "Spring Boot")
    db = selected_stack.get("database", "PostgreSQL")
    runtime = selected_stack.get("runtime", "Java 17")
    messaging = selected_stack.get("messaging", "Apache Kafka")
    orm = selected_stack.get("orm", "Spring Data JPA")
    build = selected_stack.get("build_tool", "Gradle")
    app_server = selected_stack.get("app_server", "Kubernetes + Docker")

    return f"""
╔══════════════════════════════════════════════════════════════════╗
║           CODEMORPH MIGRATION MINDMAP (BASE BLUEPRINT)          ║
╚══════════════════════════════════════════════════════════════════╝

MIGRATION GOAL
  Legacy monolith → Modern cloud-native microservices

LAYER MAPPING
  ┌─────────────────────────────────────────────────────────────┐
  │ PRESENTATION LAYER                                          │
  │   Legacy  : JSF / JSP / Thymeleaf / AngularJS              │
  │   Target  : {frontend:<50} │
  │   Pattern : SPA with REST API consumption                   │
  │   Key     : Convert managed beans → hooks/state            │
  ├─────────────────────────────────────────────────────────────┤
  │ APPLICATION / SERVICE LAYER                                 │
  │   Legacy  : Java EE EJB / Spring MVC / Servlet             │
  │   Target  : {backend:<50} │
  │   Runtime : {runtime:<50} │
  │   Pattern : RESTful microservices, @Service, @RestController│
  │   Key     : @Stateless→@Service, @EJB→@Autowired           │
  ├─────────────────────────────────────────────────────────────┤
  │ DATA ACCESS LAYER                                           │
  │   Legacy  : OpenJPA / Hibernate / raw JDBC / EclipseLink   │
  │   Target  : {orm:<50} │
  │   Database: {db:<50} │
  │   Pattern : Repository pattern, @Repository, JpaRepository │
  │   Key     : Keep @Entity/@Table, add @Transactional        │
  ├─────────────────────────────────────────────────────────────┤
  │ MESSAGING / INTEGRATION LAYER                               │
  │   Legacy  : IBM MQ / ActiveMQ / SOAP / JAX-WS              │
  │   Target  : {messaging:<50} │
  │   Pattern : Event-driven, @KafkaListener, @RabbitListener  │
  │   Key     : Replace JMS with modern broker client          │
  ├─────────────────────────────────────────────────────────────┤
  │ BUILD & DEPLOYMENT                                          │
  │   Legacy  : Maven / Ant / WAR deployment on WebSphere      │
  │   Target  : {build:<50} │
  │   Infra   : {app_server:<50} │
  │   Pattern : Containerised, 12-factor app, health endpoints  │
  └─────────────────────────────────────────────────────────────┘

UNIVERSAL CONVERSION RULES (apply to every file)
  1. Preserve ALL business logic — never remove domain code
  2. Maintain API contracts — same HTTP paths, methods, payloads
  3. Keep database schema intact — only migrate access patterns
  4. Replace XML config with annotation/property-based config
  5. Use constructor injection over field injection
  6. Add proper error handling with @ControllerAdvice / middleware
  7. Include all necessary imports in the output file
  8. Generate complete, compilable/runnable code — no stubs
  9. Translate comments to target language conventions
  10. Follow target framework's idiomatic naming conventions

ANNOTATION QUICK-REFERENCE
  @Stateless          → @Service
  @Stateful           → @Component + @Scope("prototype")
  @MessageDriven      → @KafkaListener / @RabbitListener
  @EJB                → @Autowired
  @PersistenceContext → @Autowired EntityManager
  @WebServlet         → @RestController + @RequestMapping
  @Path               → @RequestMapping
  @GET/@POST/...      → @GetMapping/@PostMapping/...
  @PathParam          → @PathVariable
  @QueryParam         → @RequestParam
  @Inject             → @Autowired
  @Named              → @Component / @Service

DATABASE MIGRATION NOTES
  - AUTO_INCREMENT    → SERIAL / GENERATED ALWAYS AS IDENTITY (PostgreSQL)
  - DATETIME          → TIMESTAMP WITH TIME ZONE
  - TINYINT(1)        → BOOLEAN
  - Backtick quotes   → Double-quote identifiers
  - IFNULL()          → COALESCE()
  - LIMIT n,m         → LIMIT m OFFSET n
"""


def _build_transform_context(
    selected_stack: dict,
    context: dict,
    analysis: dict,
    rag_context: str,
) -> str:
    """Build a compact context string for the LLM transformation prompt.

    Deliberately kept short — the full mindmap is no longer included here
    to reduce prompt token count and avoid timeouts.
    """
    parts = [
        "CONTEXT INFORMATION:",
        f"Target stack: {json.dumps(selected_stack)}",
        f"Components: {context.get('total_components', 0)}",
        f"API endpoints: {len(analysis.get('apis', []))}",
        f"Database tables: {len(analysis.get('tables', []))}",
    ]

    if rag_context:
        parts.append(f"Related context:\n{rag_context[:600]}")

    return "\n".join(parts)


async def _transform_file(
    client: AsyncGroq,
    deployment: str,
    file_path: str,
    content: str,
    source: str,
    target: str,
    context_info: str,
    force_single_chunk: bool = False,
) -> str:
    """Transform a single file using Groq (async).

    Large files are split at function/class boundaries and transformed in
    chunks so no business logic is silently truncated.
    force_single_chunk=True skips chunking (used on timeout retry with pre-trimmed content).
    """
    from app.services.functional_verifier import _static_extract
    static_rules = _static_extract(content)
    rules_contract = _build_rules_contract(static_rules)

    if force_single_chunk:
        chunks = [content]
    else:
        chunks = _split_into_chunks(content, max_chars=20000)

    if len(chunks) == 1:
        return await _transform_chunk(
            client, deployment, file_path, chunks[0],
            source, target, context_info, rules_contract,
            chunk_index=0, total_chunks=1,
        )

    logger.info(f"Splitting {file_path} into {len(chunks)} chunks for transformation")
    transformed_chunks = []
    for i, chunk in enumerate(chunks):
        try:
            transformed_chunk = await _transform_chunk(
                client, deployment, file_path, chunk,
                source, target, context_info, rules_contract,
                chunk_index=i, total_chunks=len(chunks),
            )
            transformed_chunks.append(transformed_chunk)
        except (APITimeoutError, asyncio.TimeoutError):
            # Chunk timed out — preserve original chunk with marker
            logger.warning(f"Chunk {i+1}/{len(chunks)} timed out for {file_path}, preserving original")
            ext = Path(file_path).suffix
            cmt = "#" if ext in (".py", ".rb", ".sh", ".yml", ".yaml") else "//"
            transformed_chunks.append(
                f"{cmt} ===== CodeMorph: chunk {i+1} timed out — original preserved =====\n" + chunk
            )
        except Exception as e:
            logger.error(f"Chunk {i+1}/{len(chunks)} failed for {file_path}: {e}")
            transformed_chunks.append(chunk)

    return _reassemble_chunks(transformed_chunks, file_path)


def _build_rules_contract(static_rules: dict) -> str:
    """Build a plain-text business rules contract from static extraction."""
    parts = []
    if static_rules.get("functions"):
        parts.append("FUNCTIONS THAT MUST BE PRESERVED:\n" +
                     "\n".join(f"  - {f}()" for f in static_rules["functions"][:30]))
    if static_rules.get("api_contracts"):
        parts.append("API CONTRACTS THAT MUST BE PRESERVED:\n" +
                     "\n".join(f"  - {a}" for a in static_rules["api_contracts"][:15]))
    if static_rules.get("validations"):
        parts.append("VALIDATION LOGIC THAT MUST BE PRESERVED:\n" +
                     "\n".join(f"  - {v}" for v in static_rules["validations"][:10]))
    if static_rules.get("data_operations"):
        parts.append("DATA OPERATIONS THAT MUST BE PRESERVED:\n" +
                     "\n".join(f"  - {d}" for d in static_rules["data_operations"][:10]))
    if static_rules.get("error_handling"):
        parts.append("ERROR HANDLING THAT MUST BE PRESERVED:\n" +
                     "\n".join(f"  - {e}" for e in static_rules["error_handling"][:10]))
    return "\n\n".join(parts) if parts else ""


def _split_into_chunks(content: str, max_chars: int = 20000) -> list[str]:
    """Split source code into logical chunks at function/class boundaries.

    Tries to split at top-level function/class definitions so each chunk
    is self-contained. Falls back to line-based splitting if needed.
    """
    if len(content) <= max_chars:
        return [content]

    lines = content.splitlines(keepends=True)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    # Patterns that indicate a top-level definition boundary
    BOUNDARY_RE = re.compile(
        r'^(?:public|private|protected|static|async\s+)?'
        r'(?:class|def|function|interface|enum|struct|record)\s+\w',
        re.MULTILINE,
    )

    for line in lines:
        # If adding this line would exceed the limit AND we're at a boundary, flush
        if current_len + len(line) > max_chars and current:
            stripped = line.lstrip()
            if BOUNDARY_RE.match(stripped) or stripped.startswith("//") or stripped.startswith("#"):
                chunks.append("".join(current))
                current = []
                current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("".join(current))

    # Safety: if any chunk is still too large, hard-split it
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars * 1.2:
            final.append(chunk)
        else:
            # Hard split at line boundaries
            sub_lines = chunk.splitlines(keepends=True)
            sub: list[str] = []
            sub_len = 0
            for sl in sub_lines:
                if sub_len + len(sl) > max_chars and sub:
                    final.append("".join(sub))
                    sub = []
                    sub_len = 0
                sub.append(sl)
                sub_len += len(sl)
            if sub:
                final.append("".join(sub))

    return final if final else [content]


def _reassemble_chunks(chunks: list[str], file_path: str) -> str:
    """Reassemble transformed chunks into a single file."""
    if not chunks:
        return ""
    if len(chunks) == 1:
        return chunks[0]

    # Remove duplicate imports/package declarations from non-first chunks
    ext = Path(file_path).suffix.lower()
    result_parts = [chunks[0]]

    for chunk in chunks[1:]:
        if ext in (".java", ".kt"):
            # Remove package/import lines from continuation chunks
            cleaned = "\n".join(
                line for line in chunk.splitlines()
                if not line.strip().startswith(("package ", "import "))
            )
            result_parts.append(cleaned)
        elif ext == ".py":
            # Remove import lines from continuation chunks
            cleaned = "\n".join(
                line for line in chunk.splitlines()
                if not line.strip().startswith(("import ", "from "))
            )
            result_parts.append(cleaned)
        else:
            result_parts.append(chunk)

    return "\n\n".join(result_parts)


async def _transform_chunk(
    client: AsyncGroq,
    deployment: str,
    file_path: str,
    chunk: str,
    source: str,
    target: str,
    context_info: str,
    rules_contract: str,
    chunk_index: int = 0,
    total_chunks: int = 1,
) -> str:
    """Transform a single chunk of a file using Groq."""
    conversion_guidelines = _get_conversion_guidelines(source, target)

    chunk_note = (
        f"\nNOTE: Chunk {chunk_index + 1}/{total_chunks}. "
        "Preserve all logic. Omit duplicate imports if not the first chunk."
        if total_chunks > 1 else ""
    )

    # Keep rules contract concise — cap at 60 lines to avoid bloating the prompt
    rules_lines = rules_contract.splitlines() if rules_contract else []
    if len(rules_lines) > 60:
        rules_contract_trimmed = "\n".join(rules_lines[:60]) + "\n  ... (truncated for brevity)"
    else:
        rules_contract_trimmed = rules_contract

    # Compact context — skip the full mindmap, just include the stack mapping
    stack_summary = context_info.split("CONTEXT INFORMATION:")[-1].strip() if "CONTEXT INFORMATION:" in context_info else context_info[:500]

    system_prompt = (
        f"You are an expert code modernization engineer. "
        f"Transform the source code from {source} to {target}.\n\n"
        f"RULES (follow strictly):\n"
        f"1. Preserve EVERY function, validation, API contract, and data operation listed in the CONTRACT\n"
        f"2. Same HTTP paths, methods, request/response shapes\n"
        f"3. Same database tables, queries, relationships\n"
        f"4. Same error handling and exception logic\n"
        f"5. Idiomatic {target} patterns — complete, compilable code, no stubs\n"
        f"6. All necessary imports and annotations included{chunk_note}\n\n"
        f"BUSINESS RULES CONTRACT (ALL MUST BE PRESERVED):\n"
        f"{rules_contract_trimmed if rules_contract_trimmed else '(see source code)'}\n\n"
        f"CONVERSION GUIDELINES:\n{conversion_guidelines[:3000]}\n\n"
        f"STACK CONTEXT:\n{stack_summary[:400]}"
    )

    user_prompt = (
        f"Transform this {source} code to {target}.\n"
        f"File: {file_path}\n\n"
        f"```\n{chunk}\n```\n\n"
        f"Output ONLY the transformed code — no explanations, no markdown fences."
    )

    api_params = {
        "model": deployment,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    }

    try:
        api_params["max_completion_tokens"] = 4096
        response = await client.chat.completions.create(**api_params)
    except Exception as e:
        error_str = str(e)
        if "max_completion_tokens" in error_str or "unsupported_parameter" in error_str:
            api_params.pop("max_completion_tokens", None)
            api_params["max_tokens"] = 4096
            response = await client.chat.completions.create(**api_params)
        else:
            raise

    result = response.choices[0].message.content or ""

    # Strip markdown code blocks if present
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:])
        if result.endswith("```"):
            result = result[:-3]

    return result.strip()


def _get_conversion_guidelines(source: str, target: str) -> str:
    """Get specific conversion guidelines for tech stack transformation."""
    
    # Define comprehensive conversion mappings
    conversion_mappings = {
        # Java EE to Spring Boot
        ("Java EE", "Spring Boot"): """
JAVA EE TO SPRING BOOT CONVERSION:

1. ANNOTATIONS:
   - @Stateless → @Service
   - @Stateful → @Component with @Scope("prototype")
   - @Entity → @Entity (keep same)
   - @PersistenceContext → @Autowired EntityManager
   - @Resource → @Autowired
   - @WebServlet → @RestController + @RequestMapping
   - @EJB → @Autowired

2. DEPENDENCY INJECTION:
   - Replace @EJB with @Autowired
   - Use constructor injection where possible
   - Add @ComponentScan to main class

3. REST ENDPOINTS:
   - @Path → @RequestMapping
   - @GET → @GetMapping
   - @POST → @PostMapping
   - @PUT → @PutMapping
   - @DELETE → @DeleteMapping
   - @PathParam → @PathVariable
   - @QueryParam → @RequestParam
   - @Consumes → @RequestMapping(consumes=...)
   - @Produces → @RequestMapping(produces=...)

4. JPA/PERSISTENCE:
   - Keep @Entity, @Table, @Column annotations
   - Replace @PersistenceContext with @Autowired EntityManager
   - Use @Repository for DAO classes
   - Add @Transactional for transaction management

5. CONFIGURATION:
   - Create application.properties/yml
   - Add @SpringBootApplication to main class
   - Use @Configuration classes instead of XML
   - Add spring-boot-starter dependencies

6. EXCEPTION HANDLING:
   - Use @ControllerAdvice for global exception handling
   - Replace JAX-RS exception mappers with @ExceptionHandler

7. VALIDATION:
   - Keep Bean Validation annotations (@NotNull, @Valid, etc.)
   - Add @Validated to controller classes
        """,
        
        # JSF to React
        ("JSF", "React"): """
JSF TO REACT CONVERSION:

1. COMPONENT STRUCTURE:
   - Convert .xhtml files to .tsx components
   - Replace <h:form> with React form handling
   - Convert managed beans to React hooks/state

2. DATA BINDING:
   - #{bean.property} → useState/useEffect hooks
   - <h:inputText value="#{bean.value}"/> → <input value={value} onChange={setValue}/>
   - <h:outputText value="#{bean.message}"/> → <span>{message}</span>

3. EVENT HANDLING:
   - action="#{bean.method}" → onClick={handleMethod}
   - <h:commandButton> → <button onClick={...}>
   - <h:commandLink> → <a href="#" onClick={...}>

4. NAVIGATION:
   - JSF navigation rules → React Router
   - outcome="page" → navigate('/page')
   - <h:link> → <Link to="/path">

5. VALIDATION:
   - JSF validators → React form validation libraries
   - <f:validateLength> → custom validation functions
   - <h:message> → error state display

6. AJAX:
   - <f:ajax> → fetch() or axios calls
   - Replace JSF partial updates with React state updates

7. LIFECYCLE:
   - @PostConstruct → useEffect(() => {}, [])
   - @PreDestroy → useEffect cleanup functions

8. STYLING:
   - Convert CSS to CSS modules or styled-components
   - Replace PrimeFaces components with Material-UI or similar
        """,
        
        # Spring MVC to FastAPI
        ("Spring MVC", "FastAPI"): """
SPRING MVC TO FASTAPI CONVERSION:

1. CONTROLLER STRUCTURE:
   - @RestController → FastAPI router
   - @RequestMapping → @app.get/@app.post/etc.
   - @PathVariable → path parameters in function signature
   - @RequestParam → Query parameters in function signature
   - @RequestBody → Pydantic model parameter

2. DEPENDENCY INJECTION:
   - @Autowired → Depends() function
   - @Service → regular Python class with Depends()
   - @Component → Python class/function

3. DATA MODELS:
   - Java POJOs → Pydantic models
   - @Entity → SQLAlchemy models
   - Bean validation → Pydantic validators

4. HTTP METHODS:
   - @GetMapping → @app.get()
   - @PostMapping → @app.post()
   - @PutMapping → @app.put()
   - @DeleteMapping → @app.delete()

5. EXCEPTION HANDLING:
   - @ControllerAdvice → @app.exception_handler()
   - Custom exceptions → HTTPException

6. CONFIGURATION:
   - application.properties → .env files or settings.py
   - @Configuration → Python configuration classes

7. DATABASE:
   - JPA repositories → SQLAlchemy with async support
   - @Transactional → database session management
   - JPQL → SQLAlchemy queries

8. VALIDATION:
   - @Valid → Pydantic automatic validation
   - Custom validators → Pydantic validator functions
        """,
        
        # MySQL to PostgreSQL
        ("MySQL", "PostgreSQL"): """
MYSQL TO POSTGRESQL CONVERSION:

1. DATA TYPES:
   - TINYINT → SMALLINT
   - MEDIUMINT → INTEGER
   - BIGINT → BIGINT (same)
   - VARCHAR(n) → VARCHAR(n) (same)
   - TEXT → TEXT (same)
   - LONGTEXT → TEXT
   - DATETIME → TIMESTAMP
   - TIMESTAMP → TIMESTAMPTZ
   - ENUM → CREATE TYPE or CHECK constraint

2. AUTO INCREMENT:
   - AUTO_INCREMENT → SERIAL or GENERATED ALWAYS AS IDENTITY
   - BIGINT AUTO_INCREMENT → BIGSERIAL

3. FUNCTIONS:
   - NOW() → CURRENT_TIMESTAMP
   - CONCAT() → || operator or CONCAT()
   - IFNULL() → COALESCE()
   - LIMIT n → LIMIT n (same)
   - LIMIT n, m → LIMIT m OFFSET n

4. QUOTES:
   - Backticks `column` → Double quotes "column"
   - Single quotes for strings (same)

5. BOOLEAN:
   - TINYINT(1) → BOOLEAN
   - 0/1 values → FALSE/TRUE

6. JSON:
   - JSON column type → JSONB (recommended)
   - JSON functions may need adjustment

7. INDEXES:
   - KEY → INDEX
   - FULLTEXT → GIN index with tsvector

8. CONSTRAINTS:
   - Same syntax mostly, but PostgreSQL is stricter
        """,
        
        # Oracle to PostgreSQL
        ("Oracle", "PostgreSQL"): """
ORACLE TO POSTGRESQL CONVERSION:

1. DATA TYPES:
   - NUMBER → NUMERIC or INTEGER
   - NUMBER(p,s) → NUMERIC(p,s)
   - VARCHAR2 → VARCHAR
   - CLOB → TEXT
   - BLOB → BYTEA
   - DATE → TIMESTAMP
   - TIMESTAMP → TIMESTAMP

2. SEQUENCES:
   - Oracle sequences → PostgreSQL sequences (similar syntax)
   - NEXTVAL('seq_name') → nextval('seq_name')

3. FUNCTIONS:
   - SYSDATE → CURRENT_TIMESTAMP
   - NVL() → COALESCE()
   - DECODE() → CASE WHEN
   - ROWNUM → ROW_NUMBER() OVER()
   - DUAL table → Not needed in PostgreSQL

4. PAGINATION:
   - ROWNUM → LIMIT/OFFSET
   - Oracle 12c+ OFFSET/FETCH → LIMIT/OFFSET

5. STORED PROCEDURES:
   - PL/SQL → PL/pgSQL
   - Different syntax for variables and control structures
   - EXCEPTION handling syntax differs

6. QUOTES:
   - Double quotes for identifiers (same)
   - Single quotes for strings (same)

7. SCHEMAS:
   - Oracle schemas → PostgreSQL schemas (similar concept)
   - User = schema in Oracle, separate in PostgreSQL
        """,
        
        # .NET Framework to .NET Core
        (".NET Framework", ".NET Core"): """
.NET FRAMEWORK TO .NET CORE CONVERSION:

1. PROJECT STRUCTURE:
   - .csproj format → SDK-style project format
   - packages.config → PackageReference in .csproj
   - Global.asax → Startup.cs

2. DEPENDENCY INJECTION:
   - Manual DI → Built-in DI container
   - Add services in ConfigureServices()
   - Constructor injection preferred

3. CONFIGURATION:
   - web.config → appsettings.json
   - ConfigurationManager → IConfiguration
   - Connection strings in appsettings.json

4. MVC CHANGES:
   - Controllers inherit from ControllerBase
   - [ApiController] attribute recommended
   - Model binding improvements
   - Built-in JSON serialization

5. ENTITY FRAMEWORK:
   - EF6 → EF Core
   - DbContext registration in DI
   - Migration commands change
   - Some LINQ methods differ

6. AUTHENTICATION:
   - ASP.NET Identity → ASP.NET Core Identity
   - Different middleware pipeline
   - JWT handling built-in

7. HOSTING:
   - IIS hosting → Kestrel with optional reverse proxy
   - Program.cs and Startup.cs pattern

8. MIDDLEWARE:
   - HTTP modules → Middleware pipeline
   - Configure() method in Startup
        """,
        
        # Angular to React
        ("Angular", "React"): """
ANGULAR TO REACT CONVERSION:

1. COMPONENT STRUCTURE:
   - @Component → React functional component
   - template → JSX return statement
   - styleUrls → CSS imports or styled-components

2. DATA BINDING:
   - {{expression}} → {expression}
   - [property]="value" → property={value}
   - (event)="handler" → onEvent={handler}
   - [(ngModel)]="value" → value + onChange

3. DIRECTIVES:
   - *ngFor → .map() in JSX
   - *ngIf → conditional rendering with &&
   - [ngClass] → className with conditional logic
   - [ngStyle] → style prop with object

4. LIFECYCLE:
   - ngOnInit → useEffect(() => {}, [])
   - ngOnDestroy → useEffect cleanup
   - ngOnChanges → useEffect with dependencies

5. SERVICES:
   - @Injectable services → custom hooks or context
   - Dependency injection → props or context
   - HTTP client → fetch or axios

6. ROUTING:
   - Angular Router → React Router
   - routerLink → Link component
   - Route guards → protected route components

7. FORMS:
   - Template-driven → controlled components
   - Reactive forms → useForm hooks (react-hook-form)
   - Validators → custom validation functions

8. STATE MANAGEMENT:
   - Services with BehaviorSubject → Context API or Redux
   - @Input/@Output → props and callbacks
        """
    }
    
    # Find the best matching conversion guideline
    source_clean = source.replace(" Components", "").replace(" Services", "").strip()
    target_clean = target.replace(" Components", "").replace(" Services", "").strip()
    
    # Try exact match first
    key = (source_clean, target_clean)
    if key in conversion_mappings:
        return conversion_mappings[key]
    
    # Try partial matches
    for (src, tgt), guidelines in conversion_mappings.items():
        if src in source_clean or source_clean in src:
            if tgt in target_clean or target_clean in tgt:
                return guidelines
    
    # Generic guidelines if no specific match found
    return f"""
GENERIC CONVERSION GUIDELINES FOR {source} TO {target}:

1. SYNTAX CONVERSION:
   - Update language-specific syntax and keywords
   - Convert data types to target language equivalents
   - Update import/include statements

2. FRAMEWORK PATTERNS:
   - Replace framework-specific annotations/decorators
   - Convert dependency injection patterns
   - Update configuration approaches

3. API PATTERNS:
   - Convert REST endpoint definitions
   - Update request/response handling
   - Maintain HTTP method mappings

4. DATA ACCESS:
   - Convert ORM/database access patterns
   - Update query syntax if needed
   - Maintain data relationships

5. ERROR HANDLING:
   - Convert exception handling patterns
   - Update error response formats
   - Maintain error propagation

6. TESTING:
   - Convert test framework syntax
   - Update assertion methods
   - Maintain test coverage

7. CONFIGURATION:
   - Convert configuration file formats
   - Update environment variable handling
   - Maintain deployment settings

8. DEPENDENCIES:
   - Update package/library references
   - Convert build tool configurations
   - Maintain version compatibility
    """


def _compute_new_path(
    original_path: str,
    mapping: dict,
    selected_stack: dict,
) -> str:
    """Compute the new file path for a transformed file."""
    category = mapping.get("category", "")
    path = Path(original_path)

    extension_map = {
        "Java": ".java",
        "Kotlin": ".kt",
        "Python": ".py",
        "TypeScript": ".ts",
        "JavaScript": ".js",
    }

    # For frontend transformations, map to appropriate directory
    if category == "frontend_framework":
        target = selected_stack.get("frontend_framework", "")
        if "React" in target or "Next" in target:
            new_ext = ".tsx"
            return f"frontend/src/components/{path.stem}{new_ext}"
        elif "Angular" in target:
            new_ext = ".ts"
            return f"frontend/src/app/{path.stem}{new_ext}"
        elif "Vue" in target:
            new_ext = ".vue"
            return f"frontend/src/components/{path.stem}{new_ext}"

    return str(path)


def create_artifact_zip(transformed_files: dict, project_name: str) -> str:
    """Create a ZIP archive of the modernized codebase.

    Returns the path to the ZIP file.
    """
    temp_dir = tempfile.mkdtemp(prefix="codemorph_artifact_")
    zip_path = os.path.join(temp_dir, f"{project_name}_modernized.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path, content in transformed_files.items():
            arcname = f"modernized-project/{file_path}"
            zf.writestr(arcname, content)

        # Add a README only if one wasn't already in the transformed files
        if not any(Path(p).name.lower() == "readme.md" for p in transformed_files):
            readme = f"""# {project_name} — Modernized Codebase

This codebase was automatically modernized by CodeMorph.

## Structure
- frontend/ — Frontend application
- backend/ — Backend services
- database/ — Database scripts and migrations
- configs/ — Configuration files
- docs/ — Documentation

## Getting Started
Refer to the migration report for detailed instructions.
"""
            zf.writestr("modernized-project/README.md", readme)

    return zip_path

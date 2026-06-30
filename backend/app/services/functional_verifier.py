"""Functional Preservation Verifier.

Uses the LLM to verify that transformed code preserves the business logic
of the original. Extracts business rules as a contract before transformation,
then verifies the transformed output satisfies that contract.
"""

import os
import re
import logging
from typing import Optional
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_client() -> Optional[AsyncGroq]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    return AsyncGroq(api_key=api_key, timeout=60.0, max_retries=2)


async def _call_llm(client: AsyncGroq, system: str, user: str) -> str:
    """Call the LLM and return the text response."""
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=2048,
    )
    return (resp.choices[0].message.content or "").strip()


# ── Business Rule Extraction ───────────────────────────────────────────────────

async def extract_business_rules(
    file_path: str,
    content: str,
    client: Optional[AsyncGroq] = None,
) -> dict:
    """Extract business rules from a source file as a verifiable contract.

    Returns a dict:
    {
        "file_path": str,
        "rules": [str, ...],          # plain-English business rules
        "functions": [str, ...],       # function/method names found
        "validations": [str, ...],     # validation logic found
        "api_contracts": [str, ...],   # HTTP endpoints / return types
        "data_operations": [str, ...], # DB / data operations
        "error_handling": [str, ...],  # error / exception handling
        "extraction_method": "llm" | "static",
    }
    """
    close_after = False
    if client is None:
        client = _get_client()
        close_after = True

    rules: dict = {
        "file_path": file_path,
        "rules": [],
        "functions": [],
        "validations": [],
        "api_contracts": [],
        "data_operations": [],
        "error_handling": [],
        "extraction_method": "static",
    }

    # Always do static extraction first (fast, no LLM cost)
    rules.update(_static_extract(content))

    if client:
        try:
            system = (
                "You are a senior software engineer specialising in code analysis. "
                "Extract the business rules and functional contracts from the given source code. "
                "Be precise and concrete — list only what the code actually does."
            )
            user = f"""Analyse this source file and extract its business rules as a structured list.

File: {file_path}

```
{content[:6000]}
```

Respond in this exact format (one item per line, no extra text):

RULES:
- <plain-English description of each business rule / behaviour>

VALIDATIONS:
- <each input validation or constraint enforced>

API_CONTRACTS:
- <each HTTP endpoint: METHOD /path → response description>

DATA_OPERATIONS:
- <each database / data operation: table, operation, condition>

ERROR_HANDLING:
- <each error case handled and how>
"""
            raw = await _call_llm(client, system, user)
            llm_rules = _parse_llm_rules(raw)
            # Merge: LLM results take priority, static fills gaps
            for key in ("rules", "validations", "api_contracts", "data_operations", "error_handling"):
                if llm_rules.get(key):
                    rules[key] = llm_rules[key]
            rules["extraction_method"] = "llm"
        except Exception as e:
            logger.warning(f"LLM rule extraction failed for {file_path}: {e}")
    return rules


def _static_extract(content: str) -> dict:
    """Fast regex-based extraction — no LLM required."""
    functions = []
    validations = []
    api_contracts = []
    data_operations = []
    error_handling = []

    for line in content.splitlines():
        s = line.strip()

        # Function / method names
        for pat in (
            r"def\s+(\w+)\s*\(",
            r"public\s+\w[\w<>\[\]]*\s+(\w+)\s*\(",
            r"private\s+\w[\w<>\[\]]*\s+(\w+)\s*\(",
            r"protected\s+\w[\w<>\[\]]*\s+(\w+)\s*\(",
            r"function\s+(\w+)\s*\(",
            r"const\s+(\w+)\s*=\s*(?:async\s*)?\(",
        ):
            m = re.search(pat, s)
            if m:
                name = m.group(1)
                if name not in ("if", "for", "while", "switch"):
                    functions.append(name)

        # Validation patterns
        if any(kw in s.lower() for kw in ("validate", "assert", "require", "check", "must", "should not", "cannot", "illegal")):
            validations.append(s[:120])

        # API contracts
        for pat in (
            r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*["\']([^"\']+)',
            r'@(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
            r'@Path\s*\(\s*["\']([^"\']+)',
        ):
            m = re.search(pat, s, re.IGNORECASE)
            if m:
                api_contracts.append(s[:120])

        # Data operations
        if any(kw in s.upper() for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "MERGE ", ".save(", ".findBy", ".delete(", "executeQuery", "createQuery")):
            data_operations.append(s[:120])

        # Error handling
        if any(kw in s.lower() for kw in ("throw", "raise", "catch", "except", "exception", "error", "httperror", "httpexception")):
            error_handling.append(s[:120])

    return {
        "functions": list(dict.fromkeys(functions))[:40],
        "validations": list(dict.fromkeys(validations))[:20],
        "api_contracts": list(dict.fromkeys(api_contracts))[:20],
        "data_operations": list(dict.fromkeys(data_operations))[:20],
        "error_handling": list(dict.fromkeys(error_handling))[:20],
    }


def _parse_llm_rules(raw: str) -> dict:
    """Parse the structured LLM response into rule lists."""
    result: dict = {
        "rules": [],
        "validations": [],
        "api_contracts": [],
        "data_operations": [],
        "error_handling": [],
    }
    current: Optional[str] = None
    section_map = {
        "RULES:": "rules",
        "VALIDATIONS:": "validations",
        "API_CONTRACTS:": "api_contracts",
        "DATA_OPERATIONS:": "data_operations",
        "ERROR_HANDLING:": "error_handling",
    }
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped in section_map:
            current = section_map[stripped]
        elif current and stripped.startswith("- "):
            result[current].append(stripped[2:].strip())
    return result


# ── Functional Equivalence Verification ───────────────────────────────────────

async def verify_functional_equivalence(
    file_path: str,
    original_content: str,
    transformed_content: str,
    business_rules: dict,
    client: Optional[AsyncGroq] = None,
) -> dict:
    """Verify that the transformed file preserves the business logic of the original.

    Returns:
    {
        "file_path": str,
        "passed": bool,
        "score": float,          # 0.0 – 1.0
        "preserved_rules": [str],
        "missing_rules": [str],
        "changed_behaviors": [str],
        "new_behaviors": [str],
        "verdict": "preserved" | "partial" | "lost",
        "summary": str,
        "verification_method": "llm" | "static",
    }
    """
    close_after = False
    if client is None:
        client = _get_client()
        close_after = True

    result = _static_verify(original_content, transformed_content, business_rules)

    if client:
        try:
            system = (
                "You are a senior software engineer performing a code review. "
                "Your task is to verify that a transformed file preserves the business logic "
                "of the original. Be strict — flag any missing or changed behaviour."
            )

            rules_text = "\n".join(f"  - {r}" for r in business_rules.get("rules", [])[:20])
            validations_text = "\n".join(f"  - {v}" for v in business_rules.get("validations", [])[:10])
            api_text = "\n".join(f"  - {a}" for a in business_rules.get("api_contracts", [])[:10])

            user = f"""Verify that the TRANSFORMED file preserves all business logic from the ORIGINAL.

File: {file_path}

## Known Business Rules (extracted from original)
{rules_text or '  (none extracted)'}

## Known Validations
{validations_text or '  (none extracted)'}

## Known API Contracts
{api_text or '  (none extracted)'}

## ORIGINAL CODE (first 3000 chars)
```
{original_content[:3000]}
```

## TRANSFORMED CODE (first 3000 chars)
```
{transformed_content[:3000]}
```

Respond in this exact format:

PRESERVED:
- <each business rule that IS correctly preserved>

MISSING:
- <each business rule that is ABSENT from the transformed code>

CHANGED:
- <each behaviour that exists but works differently>

NEW:
- <any new behaviour added that was not in the original>

VERDICT: preserved | partial | lost
SCORE: <0.0 to 1.0>
SUMMARY: <one sentence>
"""
            raw = await _call_llm(client, system, user)
            llm_result = _parse_verification_response(raw)
            if llm_result:
                result.update(llm_result)
                result["verification_method"] = "llm"
        except Exception as e:
            logger.warning(f"LLM verification failed for {file_path}: {e}")

    return result


def _static_verify(original: str, transformed: str, rules: dict) -> dict:
    """Fast static verification — checks function names and key patterns."""
    orig_funcs = set(rules.get("functions", []))
    trans_funcs = set(_static_extract(transformed).get("functions", []))

    preserved = list(orig_funcs & trans_funcs)
    missing   = list(orig_funcs - trans_funcs)

    # Check API contracts
    orig_apis = set(rules.get("api_contracts", []))
    trans_apis_raw = _static_extract(transformed).get("api_contracts", [])
    # Fuzzy: check if path strings from original appear in transformed
    preserved_apis = []
    missing_apis   = []
    for api in orig_apis:
        # Extract path-like tokens
        tokens = re.findall(r'/[\w/{}_-]+', api)
        if any(t in transformed for t in tokens):
            preserved_apis.append(api)
        else:
            missing_apis.append(api)

    total = len(orig_funcs) + len(orig_apis)
    preserved_count = len(preserved) + len(preserved_apis)
    score = preserved_count / total if total > 0 else 1.0

    verdict = "preserved" if score >= 0.8 else "partial" if score >= 0.5 else "lost"

    return {
        "file_path": rules.get("file_path", ""),
        "passed": score >= 0.7,
        "score": round(score, 3),
        "preserved_rules": preserved + preserved_apis,
        "missing_rules": missing + missing_apis,
        "changed_behaviors": [],
        "new_behaviors": [],
        "verdict": verdict,
        "summary": f"Static check: {preserved_count}/{total} functions/contracts preserved.",
        "verification_method": "static",
    }


def _parse_verification_response(raw: str) -> Optional[dict]:
    """Parse the structured LLM verification response."""
    result: dict = {
        "preserved_rules": [],
        "missing_rules": [],
        "changed_behaviors": [],
        "new_behaviors": [],
        "verdict": "partial",
        "score": 0.5,
        "summary": "",
    }
    current = None
    section_map = {
        "PRESERVED:": "preserved_rules",
        "MISSING:": "missing_rules",
        "CHANGED:": "changed_behaviors",
        "NEW:": "new_behaviors",
    }
    for line in raw.splitlines():
        s = line.strip()
        if s in section_map:
            current = section_map[s]
        elif s.startswith("VERDICT:"):
            v = s.split(":", 1)[1].strip().lower()
            if v in ("preserved", "partial", "lost"):
                result["verdict"] = v
        elif s.startswith("SCORE:"):
            try:
                result["score"] = float(s.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif s.startswith("SUMMARY:"):
            result["summary"] = s.split(":", 1)[1].strip()
        elif current and s.startswith("- "):
            result[current].append(s[2:].strip())

    result["passed"] = result["score"] >= 0.7
    return result


# ── API Contract Verification ──────────────────────────────────────────────────

def verify_api_contracts(
    original_apis: list,
    transformed_content_map: dict,
) -> dict:
    """Verify that all original API endpoints are present in the transformed codebase.

    original_apis: list of {method, path, handler, file, ...}
    transformed_content_map: {file_path: content}

    Returns:
    {
        "total_endpoints": int,
        "preserved_endpoints": int,
        "missing_endpoints": [{"method", "path", "original_file"}],
        "preservation_rate": float,
        "passed": bool,
    }
    """
    all_transformed = "\n".join(transformed_content_map.values())
    missing = []
    preserved = 0

    for ep in original_apis:
        path = ep.get("path", "")
        method = ep.get("method", "GET").upper()
        # Check if the path appears in any transformed file
        path_tokens = [t for t in path.split("/") if t and "{" not in t]
        found = any(token in all_transformed for token in path_tokens) if path_tokens else (path in all_transformed)
        if found:
            preserved += 1
        else:
            missing.append({
                "method": method,
                "path": path,
                "original_file": ep.get("file", ep.get("file_path", "")),
            })

    total = len(original_apis)
    rate = preserved / total if total > 0 else 1.0

    return {
        "total_endpoints": total,
        "preserved_endpoints": preserved,
        "missing_endpoints": missing,
        "preservation_rate": round(rate, 3),
        "passed": rate >= 0.9,
    }


# ── Batch Processing ───────────────────────────────────────────────────────────

async def run_full_preservation_check(
    original_files: list,
    transformed_files: dict,
    original_apis: list,
) -> dict:
    """Run the complete functional preservation check across all files.

    original_files: list of {path, content, language, ...}
    transformed_files: {new_path: content}
    original_apis: list of API endpoint dicts

    Returns a comprehensive preservation report.
    """
    client = _get_client()
    close_client = client is not None

    file_results = []
    total_score = 0.0
    files_checked = 0

    # Build a map from original path to content
    orig_map = {f["path"]: f.get("content", "") for f in original_files}

    # Build a map from stem → transformed content for matching
    trans_stem_map: dict = {}
    for tp, tc in transformed_files.items():
        import os as _os
        stem = _os.path.splitext(_os.path.basename(tp))[0].lower()
        trans_stem_map[stem] = tc

    # Only verify source code files (skip config, docs, etc.)
    CODE_EXTS = {".java", ".py", ".js", ".ts", ".jsx", ".tsx", ".cs", ".go", ".rb", ".php", ".kt"}
    import os as _os
    source_files = [
        f for f in original_files
        if _os.path.splitext(f.get("path", ""))[1].lower() in CODE_EXTS
        and f.get("content", "")
    ]

    for orig_file in source_files[:30]:  # cap at 30 files to control LLM cost
        orig_path = orig_file["path"]
        orig_content = orig_file.get("content", "")
        if not orig_content:
            continue

        # Find matching transformed file
        stem = _os.path.splitext(_os.path.basename(orig_path))[0].lower()
        trans_content = trans_stem_map.get(stem, "")

        if not trans_content:
            # File was not transformed — mark as missing
            file_results.append({
                "file_path": orig_path,
                "passed": False,
                "score": 0.0,
                "verdict": "lost",
                "summary": "No corresponding transformed file found.",
                "missing_rules": ["entire file missing from output"],
                "preserved_rules": [],
                "changed_behaviors": [],
                "new_behaviors": [],
                "verification_method": "static",
            })
            files_checked += 1
            continue

        # Extract business rules from original
        rules = await extract_business_rules(orig_path, orig_content, client)

        # Verify equivalence
        verification = await verify_functional_equivalence(
            orig_path, orig_content, trans_content, rules, client
        )
        file_results.append(verification)
        total_score += verification.get("score", 0.0)
        files_checked += 1

    if close_client and client:
        await client.close()

    # API contract check
    api_check = verify_api_contracts(original_apis, transformed_files)

    # Aggregate
    avg_score = total_score / files_checked if files_checked > 0 else 1.0
    passed_files = sum(1 for r in file_results if r.get("passed"))
    failed_files = [r for r in file_results if not r.get("passed")]

    overall_passed = avg_score >= 0.75 and api_check["passed"]

    return {
        "overall_passed": overall_passed,
        "overall_score": round(avg_score, 3),
        "files_checked": files_checked,
        "files_passed": passed_files,
        "files_failed": len(failed_files),
        "file_results": file_results,
        "api_contract_check": api_check,
        "failed_files_summary": [
            {
                "file": r["file_path"],
                "verdict": r["verdict"],
                "missing": r.get("missing_rules", [])[:5],
                "summary": r.get("summary", ""),
            }
            for r in failed_files[:20]
        ],
        "preservation_rate": round(avg_score * 100, 1),
        "api_preservation_rate": round(api_check["preservation_rate"] * 100, 1),
    }

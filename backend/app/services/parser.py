"""Tree-sitter AST Parsing Service.

Parses each file's AST using tree-sitter with appropriate language grammar.
Extracts: functions, classes, imports, dependencies, API endpoint declarations,
DB calls, SQL queries, framework-specific patterns.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import tree-sitter; fall back to regex-based parsing if unavailable
TREE_SITTER_AVAILABLE = False
_ts_parsers: dict = {}

try:
    from tree_sitter import Language, Parser as TSParser
    import tree_sitter_python as tspython
    import tree_sitter_java as tsjava
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript

    _LANG_PYTHON = Language(tspython.language())
    _LANG_JAVA = Language(tsjava.language())
    _LANG_JS = Language(tsjavascript.language_javascript())
    _LANG_TS = Language(tstypescript.language_typescript())

    _ts_parsers = {
        "Python": TSParser(_LANG_PYTHON),
        "Java": TSParser(_LANG_JAVA),
        "JavaScript": TSParser(_LANG_JS),
        "TypeScript": TSParser(_LANG_TS),
    }
    TREE_SITTER_AVAILABLE = True
    logger.info("tree-sitter loaded successfully for Python, Java, JavaScript, TypeScript")
except Exception as _ts_err:
    logger.debug(f"tree-sitter not available ({_ts_err}), using regex-based parsing")

# Language-specific regex patterns for fallback parsing
JAVA_PATTERNS = {
    "class": re.compile(r"(?:public\s+|abstract\s+|final\s+)*class\s+(\w+)"),
    "interface": re.compile(r"(?:public\s+)?interface\s+(\w+)"),
    "method": re.compile(r"(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\],\s]+\s+(\w+)\s*\("),
    "import": re.compile(r"import\s+([\w.]+(?:\.\*)?);"),
    "annotation": re.compile(r"@(\w+)(?:\(.*?\))?"),
    "rest_endpoint": re.compile(r'@(?:Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'),
    "request_mapping": re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'),
    "ejb": re.compile(r"@(?:Stateless|Stateful|Singleton|MessageDriven)"),
    "entity": re.compile(r'@Entity(?:\s*\(\s*name\s*=\s*"(\w+)"\s*\))?'),
    "table": re.compile(r'@Table\s*\(\s*name\s*=\s*"(\w+)"'),
    "sql_query": re.compile(r'(?:createQuery|createNativeQuery|@NamedQuery)\s*\(\s*"([^"]+)"'),
    "jpa_repository": re.compile(r"extends\s+(?:JpaRepository|CrudRepository|PagingAndSortingRepository)<(\w+)"),
}

PYTHON_PATTERNS = {
    "class": re.compile(r"class\s+(\w+)"),
    "function": re.compile(r"def\s+(\w+)\s*\("),
    "import": re.compile(r"(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s]+)"),
    "decorator": re.compile(r"@(\w+)(?:\(.*?\))?"),
    "flask_route": re.compile(r'@\w+\.route\s*\(\s*["\']([^"\']+)["\']'),
    "fastapi_route": re.compile(r'@\w+\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'),
    "django_url": re.compile(r'path\s*\(\s*["\']([^"\']+)["\']'),
    "sql_query": re.compile(r'(?:execute|cursor\.execute)\s*\(\s*["\']([^"\']+)["\']'),
    "sqlalchemy_model": re.compile(r"class\s+(\w+)\(.*(?:Base|Model|db\.Model).*\)"),
}

JS_TS_PATTERNS = {
    "class": re.compile(r"(?:export\s+)?class\s+(\w+)"),
    "function": re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)"),
    "arrow_function": re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("),
    "import": re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]"),
    "require": re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]"),
    "express_route": re.compile(r"(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"),
    "react_component": re.compile(r"(?:export\s+)?(?:default\s+)?(?:function|const)\s+(\w+).*?(?:React|JSX|tsx)"),
}

CSHARP_PATTERNS = {
    "class": re.compile(r"(?:public\s+|internal\s+|private\s+)?(?:abstract\s+|sealed\s+)?class\s+(\w+)"),
    "method": re.compile(r"(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?[\w<>\[\],\s]+\s+(\w+)\s*\("),
    "import": re.compile(r"using\s+([\w.]+);"),
    "attribute": re.compile(r"\[(\w+)(?:\(.*?\))?\]"),
    "api_route": re.compile(r'\[(?:Http(?:Get|Post|Put|Delete|Patch)|Route)\s*\(\s*"([^"]+)"'),
    "entity": re.compile(r'\[Table\s*\(\s*"(\w+)"\s*\)\]'),
}

SQL_PATTERNS = {
    "create_table": re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\w+\.)?(\w+)", re.IGNORECASE),
    "create_view": re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:\w+\.)?(\w+)", re.IGNORECASE),
    "create_procedure": re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(?:\w+\.)?(\w+)", re.IGNORECASE),
    "create_function": re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:\w+\.)?(\w+)", re.IGNORECASE),
    "create_index": re.compile(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:\w+\.)?(\w+)\s+ON\s+(?:\w+\.)?(\w+)", re.IGNORECASE),
    "alter_table": re.compile(r"ALTER\s+TABLE\s+(?:\w+\.)?(\w+)", re.IGNORECASE),
    "foreign_key": re.compile(r"FOREIGN\s+KEY\s*\((\w+)\)\s*REFERENCES\s+(?:\w+\.)?(\w+)\s*\((\w+)\)", re.IGNORECASE),
    "column_def": re.compile(r"^\s+(\w+)\s+(VARCHAR|INT|INTEGER|BIGINT|DECIMAL|NUMERIC|DATE|TIMESTAMP|BOOLEAN|TEXT|CLOB|BLOB|CHAR|FLOAT|DOUBLE)", re.IGNORECASE | re.MULTILINE),
}

GO_PATTERNS = {
    "function": re.compile(r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\("),
    "struct": re.compile(r"type\s+(\w+)\s+struct"),
    "interface": re.compile(r"type\s+(\w+)\s+interface"),
    "import": re.compile(r'"([\w./\-]+)"'),
}

COBOL_PATTERNS = {
    "program_id": re.compile(r"PROGRAM-ID\.\s+(\w+)", re.IGNORECASE),
    "section": re.compile(r"(\w+)\s+SECTION\.", re.IGNORECASE),
    "paragraph": re.compile(r"^       (\w[\w-]+)\.", re.MULTILINE),
    "copy": re.compile(r"COPY\s+(\w+)", re.IGNORECASE),
    "call": re.compile(r"CALL\s+['\"](\w+)['\"]", re.IGNORECASE),
    "sql_exec": re.compile(r"EXEC\s+SQL(.*?)END-EXEC", re.IGNORECASE | re.DOTALL),
}


def _extract_with_tree_sitter(content: str, language: str) -> dict:
    """Use tree-sitter to extract structural info from source code."""
    parser = _ts_parsers.get(language)
    if not parser:
        return {}

    try:
        tree = parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        classes, functions, imports = [], [], []

        def walk(node):
            t = node.type
            # Classes / interfaces
            if t in ("class_declaration", "class_definition", "interface_declaration"):
                for child in node.children:
                    if child.type in ("identifier", "type_identifier"):
                        classes.append({
                            "name": child.text.decode("utf8"),
                            "type": "class",
                            "line": node.start_point[0] + 1,
                        })
                        break
            # Functions / methods
            elif t in ("function_definition", "method_declaration", "function_declaration",
                       "method_definition", "arrow_function"):
                for child in node.children:
                    if child.type == "identifier":
                        functions.append({
                            "name": child.text.decode("utf8"),
                            "type": t,
                            "line": node.start_point[0] + 1,
                        })
                        break
            # Imports
            elif t in ("import_statement", "import_declaration", "import_from_statement"):
                imports.append(node.text.decode("utf8", errors="ignore").strip())

            for child in node.children:
                walk(child)

        walk(root)
        return {"classes": classes, "functions": functions, "imports": imports}
    except Exception as e:
        logger.debug(f"tree-sitter extraction failed for {language}: {e}")
        return {}


def _run_regex_extras(content: str, language: str, path: str, patterns: dict, result: dict):
    """Run regex-based extraction for annotations, endpoints, SQL, entities, tables.
    Used to complement tree-sitter results which don't cover framework-specific patterns.
    """
    # Annotations/decorators
    for pattern_name in ["annotation", "decorator", "attribute"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                result["annotations"].append(match.group(1))

    # REST endpoints
    for pattern_name in ["rest_endpoint", "request_mapping", "flask_route",
                          "fastapi_route", "express_route", "api_route", "django_url"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                method = "GET"
                raw = match.group(0)
                if "post" in pattern_name.lower() or "Post" in raw:
                    method = "POST"
                elif "put" in pattern_name.lower() or "Put" in raw:
                    method = "PUT"
                elif "delete" in pattern_name.lower() or "Delete" in raw:
                    method = "DELETE"
                elif "patch" in pattern_name.lower() or "Patch" in raw:
                    method = "PATCH"
                result["endpoints"].append({
                    "path": match.group(1),
                    "method": method,
                    "handler": path,
                    "type": "REST",
                })

    # SQL queries
    for pattern_name in ["sql_query", "sql_exec"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                result["sql_queries"].append(match.group(1).strip())

    # ORM entities
    for pattern_name in ["entity", "sqlalchemy_model"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                result["entities"].append({
                    "name": match.group(1) if match.group(1) else "Unknown",
                    "file": path,
                })

    # Table definitions
    for pattern_name in ["create_table", "create_view", "create_procedure", "create_function"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                obj_type = pattern_name.replace("create_", "").capitalize()
                result["tables"].append({
                    "name": match.group(1),
                    "type": obj_type,
                    "file": path,
                })

    if "table" in patterns:
        for match in patterns["table"].finditer(content):
            result["tables"].append({
                "name": match.group(1),
                "type": "Entity",
                "file": path,
            })

    # EJB patterns
    if "ejb" in patterns:
        for match in patterns["ejb"].finditer(content):
            result["framework_patterns"].append({
                "type": "EJB",
                "pattern": match.group(0),
                "file": path,
            })

    # JPA repositories
    if "jpa_repository" in patterns:
        for match in patterns["jpa_repository"].finditer(content):
            result["framework_patterns"].append({
                "type": "JPA_Repository",
                "entity": match.group(1),
                "file": path,
            })


def get_patterns_for_language(language: str) -> dict:
    lang_patterns = {
        "Java": JAVA_PATTERNS,
        "Python": PYTHON_PATTERNS,
        "JavaScript": JS_TS_PATTERNS,
        "TypeScript": JS_TS_PATTERNS,
        "C#": CSHARP_PATTERNS,
        "SQL": SQL_PATTERNS,
        "PL/SQL": SQL_PATTERNS,
        "Go": GO_PATTERNS,
        "COBOL": COBOL_PATTERNS,
    }
    return lang_patterns.get(language, {})


def parse_file(file_info: dict) -> dict:
    """Parse a single file and extract structural information.

    Returns structured parse results with classes, functions, imports, etc.
    """
    content = file_info.get("content", "")
    language = file_info.get("language", "Other")
    path = file_info.get("path", "")

    result = {
        "path": path,
        "language": language,
        "classes": [],
        "functions": [],
        "imports": [],
        "annotations": [],
        "endpoints": [],
        "sql_queries": [],
        "entities": [],
        "tables": [],
        "dependencies": [],
        "framework_patterns": [],
    }

    if not content:
        return result

    patterns = get_patterns_for_language(language)
    if not patterns:
        return result

    # --- Tree-sitter enrichment (when available) ---
    if TREE_SITTER_AVAILABLE and language in _ts_parsers:
        ts_data = _extract_with_tree_sitter(content, language)
        if ts_data:
            # Merge tree-sitter results; they take priority for classes/functions/imports
            result["classes"] = ts_data.get("classes", [])
            result["functions"] = ts_data.get("functions", [])
            # Keep raw import strings for framework detection
            result["imports"] = ts_data.get("imports", [])
            # Still run regex for endpoints, SQL, entities, annotations
            _run_regex_extras(content, language, path, patterns, result)
            _detect_frameworks(content, language, result)
            return result
    # --- Regex-only path ---

    # Extract classes
    for pattern_name in ["class", "struct", "interface", "program_id"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                result["classes"].append({
                    "name": match.group(1),
                    "type": pattern_name,
                    "line": content[:match.start()].count("\n") + 1,
                })

    # Extract functions/methods
    for pattern_name in ["method", "function", "arrow_function", "paragraph"]:
        if pattern_name in patterns:
            for match in patterns[pattern_name].finditer(content):
                result["functions"].append({
                    "name": match.group(1),
                    "type": pattern_name,
                    "line": content[:match.start()].count("\n") + 1,
                })

    # Extract imports
    if "import" in patterns:
        for match in patterns["import"].finditer(content):
            groups = match.groups()
            import_name = next((g for g in groups if g), "")
            result["imports"].append(import_name)

    if "require" in patterns:
        for match in patterns["require"].finditer(content):
            result["imports"].append(match.group(1))

    if "copy" in patterns:
        for match in patterns["copy"].finditer(content):
            result["imports"].append(match.group(1))

    # Run shared regex extras (annotations, endpoints, SQL, entities, tables, EJB, JPA)
    _run_regex_extras(content, language, path, patterns, result)
    _detect_frameworks(content, language, result)

    # Detect JPA repositories
    if "jpa_repository" in patterns:
        for match in patterns["jpa_repository"].finditer(content):
            result["framework_patterns"].append({
                "type": "JPA_Repository",
                "entity": match.group(1),
                "file": path,
            })

    return result


def _detect_frameworks(content: str, language: str, result: dict):
    """Detect framework-specific patterns in source code."""
    framework_indicators = {
        "Spring Boot": [
            "@SpringBootApplication", "@RestController", "@Service",
            "@Repository", "@Autowired", "@Component",
        ],
        "Spring MVC": ["@Controller", "@RequestMapping", "ModelAndView"],
        "Java EE / EJB": [
            "@Stateless", "@Stateful", "@MessageDriven",
            "@EJB", "@Resource", "@PersistenceContext",
        ],
        "JSF": ["@ManagedBean", "@ViewScoped", "xmlns.jcp.org/jsf", "h:form", "f:view"],
        "JSP": ["<%@", "<%=", "<jsp:", "pageContext"],
        "Hibernate": [
            "@Entity", "@Table", "@Column", "SessionFactory",
            "hibernate.cfg.xml", "org.hibernate",
        ],
        "JPA / OpenJPA": [
            "javax.persistence", "jakarta.persistence", "@PersistenceContext",
            "EntityManager", "openjpa",
        ],
        "SOAP / JAX-WS": ["@WebService", "@WebMethod", "wsdl", "SOAPMessage"],
        "Django": ["from django", "urlpatterns", "models.Model", "INSTALLED_APPS"],
        "Flask": ["from flask", "Flask(__name__)", "@app.route"],
        "FastAPI": ["from fastapi", "FastAPI()", "@app.get"],
        "Express": ["express()", "app.listen", "router.get"],
        "React": ["import React", "from 'react'", "useState", "useEffect"],
        "Angular": ["@Component", "@NgModule", "from '@angular"],
        "Vue": ["createApp", "defineComponent", "from 'vue'"],
        "ASP.NET": ["Microsoft.AspNetCore", "[ApiController]", "IActionResult"],
    }

    for framework, indicators in framework_indicators.items():
        for indicator in indicators:
            if indicator in content:
                result["framework_patterns"].append({
                    "type": "framework",
                    "framework": framework,
                    "indicator": indicator,
                })
                break


def parse_files(files: list[dict]) -> list[dict]:
    """Parse a list of files and return parse results."""
    results = []
    for f in files:
        try:
            result = parse_file(f)
            results.append(result)
        except Exception as e:
            logger.error(f"Error parsing {f.get('path', 'unknown')}: {e}")
            results.append({
                "path": f.get("path", ""),
                "language": f.get("language", ""),
                "error": str(e),
                "classes": [], "functions": [], "imports": [],
                "annotations": [], "endpoints": [], "sql_queries": [],
                "entities": [], "tables": [], "dependencies": [],
                "framework_patterns": [],
            })
    return results

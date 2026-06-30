"""Codebase Ingestion Service.

Accepts a local path or Git URL, recursively traverses all files,
detects file types, and filters relevant source files.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

SUPPORTED_EXTENSIONS = {
    # Languages
    ".java", ".py", ".js", ".jsx", ".ts", ".tsx", ".cs", ".cpp", ".c", ".h",
    ".go", ".rs", ".cbl", ".cob", ".cobol",
    # SQL / DB
    ".sql", ".ddl", ".plsql",
    # Web
    ".html", ".htm", ".css", ".scss", ".less", ".jsp", ".jsf", ".xhtml",
    # Config / Build
    ".xml", ".yaml", ".yml", ".json", ".properties", ".toml", ".ini", ".cfg",
    ".gradle", ".sbt",
    # Infra
    ".sh", ".bash", ".bat", ".ps1",
    # Docs
    ".md", ".txt", ".rst",
}

IMPORTANT_FILES = {
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json",
    "web.xml", "application.properties", "application.yml",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Makefile", "CMakeLists.txt", "Cargo.toml", "go.mod", "go.sum",
    "requirements.txt", "setup.py", "pyproject.toml",
    ".gitignore", "tsconfig.json", "webpack.config.js", "vite.config.ts",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", ".settings", "target", "build", "dist",
    "out", "bin", "obj", ".gradle", ".mvn",
}

BINARY_EXTENSIONS = {
    ".class", ".jar", ".war", ".ear", ".exe", ".dll", ".so", ".dylib",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".bmp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo",
}


def clone_repo(url: str) -> str:
    """Clone a git repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="codemorph_")
    subprocess.run(
        ["git", "clone", "--depth", "1", url, temp_dir],
        check=True,
        capture_output=True,
        timeout=300,
    )
    return temp_dir


def is_relevant_file(file_path: Path) -> bool:
    """Check if a file is relevant for analysis."""
    name = file_path.name
    ext = file_path.suffix.lower()

    if name in IMPORTANT_FILES:
        return True
    if ext in SUPPORTED_EXTENSIONS:
        return True
    if name == "Dockerfile":
        return True
    return False


def count_lines(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def detect_language(file_path: Path) -> str:
    """Detect the programming language from file extension."""
    ext = file_path.suffix.lower()
    name = file_path.name

    lang_map = {
        ".java": "Java", ".py": "Python", ".js": "JavaScript",
        ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".h": "C/C++",
        ".go": "Go", ".rs": "Rust",
        ".cbl": "COBOL", ".cob": "COBOL", ".cobol": "COBOL",
        ".sql": "SQL", ".ddl": "SQL", ".plsql": "PL/SQL",
        ".html": "HTML", ".htm": "HTML", ".css": "CSS",
        ".scss": "SCSS", ".less": "LESS",
        ".jsp": "JSP", ".jsf": "JSF", ".xhtml": "XHTML",
        ".xml": "XML", ".yaml": "YAML", ".yml": "YAML",
        ".json": "JSON", ".properties": "Properties",
        ".toml": "TOML", ".ini": "INI",
        ".gradle": "Gradle", ".sh": "Shell", ".bash": "Shell",
        ".bat": "Batch", ".ps1": "PowerShell",
        ".md": "Markdown",
    }

    if name == "Dockerfile":
        return "Dockerfile"
    return lang_map.get(ext, "Other")


def ingest_codebase(source_path: str) -> dict:
    """Ingest a codebase from a local path or Git URL.

    Returns a dict with:
      - files: list of file info dicts
      - total_files: int
      - total_loc: int
      - language_distribution: dict of lang -> LOC
      - source_path: resolved local path
    """
    # If it looks like a URL, clone it
    actual_path = source_path
    if source_path.startswith("http://") or source_path.startswith("https://") or source_path.endswith(".git"):
        actual_path = clone_repo(source_path)

    root = Path(actual_path)
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {actual_path}")

    files = []
    language_loc: dict[str, int] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out skip directories in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if not is_relevant_file(file_path):
                continue

            rel_path = str(file_path.relative_to(root))
            lang = detect_language(file_path)
            loc = count_lines(file_path)

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            files.append({
                "path": rel_path,
                "absolute_path": str(file_path),
                "language": lang,
                "loc": loc,
                "size": file_path.stat().st_size,
                "extension": file_path.suffix.lower(),
                "filename": filename,
                "content": content,
            })

            language_loc[lang] = language_loc.get(lang, 0) + loc

    total_loc = sum(f["loc"] for f in files)

    # Convert to percentages
    language_distribution = {}
    if total_loc > 0:
        for lang, loc in sorted(language_loc.items(), key=lambda x: -x[1]):
            language_distribution[lang] = round((loc / total_loc) * 100, 1)

    return {
        "files": files,
        "total_files": len(files),
        "total_loc": total_loc,
        "language_distribution": language_distribution,
        "source_path": actual_path,
    }

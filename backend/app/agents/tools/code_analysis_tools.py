"""Code Analysis Tools for Analysis Agent."""

import ast
import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysisInput:
    """Input for code analysis tools."""
    code: str
    language: str = "python"
    file_path: Optional[str] = None


class ASTAnalysisTool(BaseTool):
    """Tool for AST-based code analysis."""
    
    name: str = "ast_analysis"
    description: str = "Analyze code using Abstract Syntax Tree parsing"
    
    def _run(self, code: str, language: str = "python", file_path: Optional[str] = None) -> Dict[str, Any]:
        """Run AST analysis on code."""
        try:
            if language.lower() != "python":
                return {"error": f"AST analysis not supported for {language}"}
            
            tree = ast.parse(code)
            
            # Extract information from AST
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.FunctionDef):
                    if not any(node.lineno >= cls_node.lineno and 
                             node.lineno <= (cls_node.end_lineno or cls_node.lineno) 
                             for cls_node in ast.walk(tree) if isinstance(cls_node, ast.ClassDef)):
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": len(node.args.args),
                            "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                        })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({"name": alias.name, "alias": alias.asname})
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            imports.append({
                                "name": f"{module}.{alias.name}" if module else alias.name,
                                "alias": alias.asname
                            })
            
            return {
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "total_lines": len(code.split('\n')),
                "file_path": file_path
            }
            
        except SyntaxError as e:
            return {"error": f"Syntax error in code: {str(e)}"}
        except Exception as e:
            logger.error(f"AST analysis failed: {e}")
            return {"error": f"AST analysis failed: {str(e)}"}
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{decorator.value.id}.{decorator.attr}" if hasattr(decorator.value, 'id') else decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return "unknown"


class ComplexityAnalysisTool(BaseTool):
    """Tool for code complexity analysis."""
    
    name: str = "complexity_analysis"
    description: str = "Analyze code complexity metrics including cyclomatic complexity"
    
    def _run(self, code: str, language: str = "python", file_path: Optional[str] = None) -> Dict[str, Any]:
        """Run complexity analysis on code."""
        try:
            if language.lower() != "python":
                return self._generic_complexity_analysis(code, language)
            
            tree = ast.parse(code)
            
            # Calculate cyclomatic complexity
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            # Calculate other metrics
            lines_of_code = len([line for line in code.split('\n') if line.strip()])
            total_lines = len(code.split('\n'))
            
            # Function-level complexity
            function_complexities = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_complexity = self._calculate_function_complexity(node)
                    function_complexities.append({
                        "name": node.name,
                        "complexity": func_complexity,
                        "line": node.lineno
                    })
            
            return {
                "cyclomatic_complexity": complexity,
                "lines_of_code": lines_of_code,
                "total_lines": total_lines,
                "average_complexity": complexity / max(len(function_complexities), 1),
                "function_complexities": function_complexities,
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return {"error": f"Complexity analysis failed: {str(e)}"}
    
    def _generic_complexity_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Generic complexity analysis for non-Python languages."""
        lines = code.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])
        
        # Simple heuristic complexity calculation
        complexity_keywords = ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', 'try']
        complexity = 1
        
        for line in lines:
            line_lower = line.lower()
            for keyword in complexity_keywords:
                complexity += line_lower.count(keyword)
        
        return {
            "cyclomatic_complexity": complexity,
            "lines_of_code": lines_of_code,
            "total_lines": len(lines),
            "language": language,
            "estimated": True
        }
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity for a specific function."""
        complexity = 1
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity

class DependencyGraphTool(BaseTool):
    """Tool for dependency graph analysis."""
    
    name: str = "dependency_graph"
    description: str = "Analyze code dependencies and build dependency graphs"
    
    def _run(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run dependency graph analysis."""
        try:
            dependencies = {}
            
            for file_info in files_data:
                file_path = file_info.get("path", "")
                content = file_info.get("content", "")
                language = file_info.get("language", "")
                
                # Extract imports/dependencies
                file_deps = self._extract_dependencies(content, language)
                dependencies[file_path] = file_deps
            
            # Build dependency graph
            graph = self._build_dependency_graph(dependencies, files_data)
            
            return {
                "dependencies": dependencies,
                "graph": graph,
                "metrics": self._calculate_graph_metrics(graph),
                "circular_dependencies": self._detect_circular_dependencies(graph)
            }
            
        except Exception as e:
            logger.error(f"Dependency graph analysis failed: {e}")
            return {"error": f"Dependency graph analysis failed: {str(e)}"}
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract dependencies from code content."""
        dependencies = []
        
        if language.lower() == "python":
            # Python imports
            import_patterns = [
                r'import\s+([^\s,]+)',
                r'from\s+([^\s]+)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        elif language.lower() in ["java"]:
            # Java imports
            pattern = r'import\s+([^;]+);'
            matches = re.findall(pattern, content)
            dependencies.extend(matches)
        
        elif language.lower() in ["javascript", "typescript"]:
            # JavaScript/TypeScript imports
            patterns = [
                r'import.*from\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)
        
        return dependencies
    
    def _build_dependency_graph(self, dependencies: Dict[str, List[str]], files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build dependency graph from extracted dependencies."""
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Create nodes
        for file_path in dependencies.keys():
            graph["nodes"].append({
                "id": file_path,
                "label": file_path.split("/")[-1],
                "type": "file"
            })
        
        # Create edges
        for file_path, deps in dependencies.items():
            for dep in deps:
                # Try to resolve dependency to actual file
                resolved_file = self._resolve_import(dep, files_data)
                if resolved_file and resolved_file in dependencies:
                    graph["edges"].append({
                        "source": file_path,
                        "target": resolved_file,
                        "type": "dependency"
                    })
        
        return graph
    
    def _resolve_import(self, import_name: str, files_data: List[Dict[str, Any]]) -> Optional[str]:
        """Resolve import name to actual file path."""
        # Simple resolution logic - can be enhanced
        for file_info in files_data:
            file_path = file_info.get("path", "")
            if import_name in file_path or file_path.endswith(f"{import_name}.py"):
                return file_path
        return None
    
    def _calculate_graph_metrics(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate graph metrics."""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
            "average_degree": (2 * len(edges)) / len(nodes) if len(nodes) > 0 else 0
        }
    
    def _detect_circular_dependencies(self, graph: Dict[str, Any]) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        # Simple cycle detection using DFS
        edges = graph.get("edges", [])
        
        # Build adjacency list
        adj_list = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source not in adj_list:
                adj_list[source] = []
            adj_list[source].append(target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj_list.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in adj_list:
            if node not in visited:
                dfs(node, [])
        
        return cycles


class PatternDetectionTool(BaseTool):
    """Tool for design pattern detection."""
    
    name: str = "pattern_detection"
    description: str = "Detect design patterns and anti-patterns in code"
    
    def _run(self, code: str, language: str = "python", file_path: Optional[str] = None) -> Dict[str, Any]:
        """Run pattern detection on code."""
        try:
            if language.lower() == "python":
                return self._detect_python_patterns(code)
            else:
                return self._detect_generic_patterns(code, language)
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return {"error": f"Pattern detection failed: {str(e)}"}
    
    def _detect_python_patterns(self, code: str) -> Dict[str, Any]:
        """Detect patterns in Python code."""
        patterns = []
        anti_patterns = []
        
        # Singleton pattern detection
        if re.search(r'class\s+\w+.*:\s*\n.*__new__', code, re.MULTILINE | re.DOTALL):
            patterns.append({
                "name": "Singleton",
                "type": "creational",
                "confidence": 0.8,
                "description": "Singleton pattern detected via __new__ method"
            })
        
        # Factory pattern detection
        if re.search(r'def\s+create_\w+|def\s+make_\w+|def\s+build_\w+', code):
            patterns.append({
                "name": "Factory",
                "type": "creational",
                "confidence": 0.6,
                "description": "Factory pattern detected via create/make/build methods"
            })
        
        # Observer pattern detection
        if re.search(r'def\s+notify|def\s+update|def\s+subscribe', code):
            patterns.append({
                "name": "Observer",
                "type": "behavioral",
                "confidence": 0.7,
                "description": "Observer pattern detected via notify/update/subscribe methods"
            })
        
        # Anti-patterns
        if re.search(r'global\s+\w+', code):
            anti_patterns.append({
                "name": "Global Variables",
                "type": "code_smell",
                "severity": "medium",
                "description": "Global variables detected"
            })
        
        # Long method anti-pattern
        methods = re.findall(r'def\s+\w+.*?(?=def|\Z)', code, re.DOTALL)
        for method in methods:
            if len(method.split('\n')) > 50:
                anti_patterns.append({
                    "name": "Long Method",
                    "type": "code_smell",
                    "severity": "high",
                    "description": "Method with more than 50 lines detected"
                })
        
        return {
            "patterns": patterns,
            "anti_patterns": anti_patterns,
            "language": "python"
        }
    
    def _detect_generic_patterns(self, code: str, language: str) -> Dict[str, Any]:
        """Detect patterns in generic code."""
        patterns = []
        
        # Generic pattern detection based on naming conventions
        if re.search(r'class\s+\w*Factory\w*|function\s+create\w+', code, re.IGNORECASE):
            patterns.append({
                "name": "Factory",
                "type": "creational",
                "confidence": 0.5,
                "description": "Factory pattern detected via naming convention"
            })
        
        return {
            "patterns": patterns,
            "anti_patterns": [],
            "language": language
        }


class SecurityAnalysisTool(BaseTool):
    """Tool for security analysis."""
    
    name: str = "security_analysis"
    description: str = "Analyze code for security vulnerabilities and issues"
    
    def _run(self, code: str, language: str = "python", file_path: Optional[str] = None) -> Dict[str, Any]:
        """Run security analysis on code."""
        try:
            if language.lower() == "python":
                return self._analyze_python_security(code)
            else:
                return self._analyze_generic_security(code, language)
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {"error": f"Security analysis failed: {str(e)}"}
    
    def _analyze_python_security(self, code: str) -> Dict[str, Any]:
        """Analyze Python code for security issues."""
        vulnerabilities = []
        
        # SQL Injection detection
        if re.search(r'execute\s*\(\s*["\'].*%.*["\']', code):
            vulnerabilities.append({
                "type": "SQL Injection",
                "severity": "high",
                "description": "Potential SQL injection via string formatting",
                "confidence": 0.8
            })
        
        # Command Injection detection
        if re.search(r'os\.system\s*\(|subprocess\.call\s*\(.*shell\s*=\s*True', code):
            vulnerabilities.append({
                "type": "Command Injection",
                "severity": "high",
                "description": "Potential command injection via os.system or subprocess",
                "confidence": 0.9
            })
        
        # Hardcoded secrets detection
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                vulnerabilities.append({
                    "type": "Hardcoded Secret",
                    "severity": "medium",
                    "description": "Hardcoded secret detected",
                    "confidence": 0.7
                })
        
        # Insecure random detection
        if re.search(r'random\.random\(\)|random\.choice\(', code):
            vulnerabilities.append({
                "type": "Weak Random",
                "severity": "low",
                "description": "Use of insecure random number generator",
                "confidence": 0.6
            })
        
        return {
            "vulnerabilities": vulnerabilities,
            "risk_score": self._calculate_risk_score(vulnerabilities),
            "language": "python"
        }
    
    def _analyze_generic_security(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze generic code for security issues."""
        vulnerabilities = []
        
        # Generic patterns
        if re.search(r'password|secret|key', code, re.IGNORECASE):
            vulnerabilities.append({
                "type": "Potential Secret",
                "severity": "low",
                "description": "Code contains potential secret-related keywords",
                "confidence": 0.3
            })
        
        return {
            "vulnerabilities": vulnerabilities,
            "risk_score": self._calculate_risk_score(vulnerabilities),
            "language": language
        }
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3
        }
        
        total_score = 0.0
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "low")
            confidence = vuln.get("confidence", 0.5)
            weight = severity_weights.get(severity, 0.3)
            total_score += weight * confidence
        
        return min(total_score, 1.0)  # Cap at 1.0
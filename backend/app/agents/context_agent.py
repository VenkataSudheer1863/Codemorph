"""Context Agent for Advanced Context Building and Pattern Detection."""

import logging
from typing import Any, Dict, List, Optional
import json

from langchain_core.tools import BaseTool, tool
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from .base_agent import BaseCodeMorphAgent, AgentResult

logger = logging.getLogger(__name__)


class ContextAnalysisInput(BaseModel):
    """Input for context analysis."""
    files: List[Dict[str, Any]] = Field(description="List of file data")
    parse_results: List[Dict[str, Any]] = Field(description="Parsed code results")
    project_info: Dict[str, Any] = Field(description="Project information")


@tool
def analyze_architecture_layers(files_data: str) -> str:
    """Analyze and classify files into architecture layers."""
    try:
        files = json.loads(files_data)
        layers = {
            "presentation": {"files": [], "patterns": [], "frameworks": []},
            "business": {"files": [], "patterns": [], "frameworks": []},
            "data": {"files": [], "patterns": [], "frameworks": []},
            "integration": {"files": [], "patterns": [], "frameworks": []},
            "infrastructure": {"files": [], "patterns": [], "frameworks": []}
        }
        
        for file_info in files:
            path = file_info.get("path", "").lower()
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            
            # Classify based on path patterns
            if any(pattern in path for pattern in ["view", "ui", "frontend", "client", "web", "html", "css", "js", "tsx", "jsx"]):
                layers["presentation"]["files"].append(file_info)
                layers["presentation"]["frameworks"].extend(_detect_frontend_frameworks(content, language))
            elif any(pattern in path for pattern in ["service", "business", "logic", "core", "domain"]):
                layers["business"]["files"].append(file_info)
                layers["business"]["patterns"].extend(_detect_business_patterns(content, language))
            elif any(pattern in path for pattern in ["data", "repository", "dao", "model", "entity", "db", "database"]):
                layers["data"]["files"].append(file_info)
                layers["data"]["patterns"].extend(_detect_data_patterns(content, language))
            elif any(pattern in path for pattern in ["api", "controller", "endpoint", "rest", "graphql", "integration"]):
                layers["integration"]["files"].append(file_info)
                layers["integration"]["patterns"].extend(_detect_integration_patterns(content, language))
            else:
                layers["infrastructure"]["files"].append(file_info)
                layers["infrastructure"]["patterns"].extend(_detect_infrastructure_patterns(content, language))
        
        return json.dumps(layers, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing architecture layers: {e}")
        return json.dumps({"error": str(e)})


def _detect_frontend_frameworks(content: str, language: str) -> List[str]:
    """Detect frontend frameworks and libraries."""
    frameworks = []
    content_lower = content.lower()
    
    if "react" in content_lower or "jsx" in content_lower:
        frameworks.append("React")
    if "vue" in content_lower:
        frameworks.append("Vue.js")
    if "angular" in content_lower:
        frameworks.append("Angular")
    if "svelte" in content_lower:
        frameworks.append("Svelte")
    if "next" in content_lower:
        frameworks.append("Next.js")
    if "nuxt" in content_lower:
        frameworks.append("Nuxt.js")
    
    return frameworks


def _detect_business_patterns(content: str, language: str) -> List[str]:
    """Detect business logic patterns."""
    patterns = []
    content_lower = content.lower()
    
    if "strategy" in content_lower:
        patterns.append("Strategy Pattern")
    if "factory" in content_lower:
        patterns.append("Factory Pattern")
    if "observer" in content_lower:
        patterns.append("Observer Pattern")
    if "command" in content_lower:
        patterns.append("Command Pattern")
    if "decorator" in content_lower:
        patterns.append("Decorator Pattern")
    
    return patterns


def _detect_data_patterns(content: str, language: str) -> List[str]:
    """Detect data access patterns."""
    patterns = []
    content_lower = content.lower()
    
    if "repository" in content_lower:
        patterns.append("Repository Pattern")
    if "dao" in content_lower:
        patterns.append("Data Access Object")
    if "orm" in content_lower or "sqlalchemy" in content_lower:
        patterns.append("ORM")
    if "migration" in content_lower:
        patterns.append("Database Migration")
    
    return patterns


def _detect_integration_patterns(content: str, language: str) -> List[str]:
    """Detect integration patterns."""
    patterns = []
    content_lower = content.lower()
    
    if "rest" in content_lower or "api" in content_lower:
        patterns.append("REST API")
    if "graphql" in content_lower:
        patterns.append("GraphQL")
    if "webhook" in content_lower:
        patterns.append("Webhook")
    if "queue" in content_lower or "message" in content_lower:
        patterns.append("Message Queue")
    
    return patterns


def _detect_infrastructure_patterns(content: str, language: str) -> List[str]:
    """Detect infrastructure patterns."""
    patterns = []
    content_lower = content.lower()
    
    if "docker" in content_lower:
        patterns.append("Docker")
    if "kubernetes" in content_lower:
        patterns.append("Kubernetes")
    if "terraform" in content_lower:
        patterns.append("Terraform")
    if "ansible" in content_lower:
        patterns.append("Ansible")
    if "ci/cd" in content_lower or "pipeline" in content_lower:
        patterns.append("CI/CD Pipeline")
    
    return patterns


@tool
def detect_cross_cutting_concerns(files_data: str) -> str:
    """Detect cross-cutting concerns across the codebase."""
    try:
        files = json.loads(files_data)
        concerns = {
            "logging": {"files": [], "patterns": []},
            "security": {"files": [], "patterns": []},
            "caching": {"files": [], "patterns": []},
            "monitoring": {"files": [], "patterns": []},
            "error_handling": {"files": [], "patterns": []},
            "configuration": {"files": [], "patterns": []}
        }
        
        for file_info in files:
            content = file_info.get("content", "").lower()
            
            # Logging
            if any(pattern in content for pattern in ["log", "logger", "logging"]):
                concerns["logging"]["files"].append(file_info["path"])
                concerns["logging"]["patterns"].extend(_detect_logging_patterns(content))
            
            # Security
            if any(pattern in content for pattern in ["auth", "security", "jwt", "oauth", "encrypt", "hash"]):
                concerns["security"]["files"].append(file_info["path"])
                concerns["security"]["patterns"].extend(_detect_security_patterns(content))
            
            # Caching
            if any(pattern in content for pattern in ["cache", "redis", "memcache"]):
                concerns["caching"]["files"].append(file_info["path"])
                concerns["caching"]["patterns"].extend(_detect_caching_patterns(content))
            
            # Monitoring
            if any(pattern in content for pattern in ["metric", "monitor", "trace", "prometheus"]):
                concerns["monitoring"]["files"].append(file_info["path"])
                concerns["monitoring"]["patterns"].extend(_detect_monitoring_patterns(content))
            
            # Error handling
            if any(pattern in content for pattern in ["try", "catch", "except", "error", "exception"]):
                concerns["error_handling"]["files"].append(file_info["path"])
                concerns["error_handling"]["patterns"].extend(_detect_error_patterns(content))
            
            # Configuration
            if any(pattern in content for pattern in ["config", "setting", "env", "property"]):
                concerns["configuration"]["files"].append(file_info["path"])
                concerns["configuration"]["patterns"].extend(_detect_config_patterns(content))
        
        return json.dumps(concerns, indent=2)
    except Exception as e:
        logger.error(f"Error detecting cross-cutting concerns: {e}")
        return json.dumps({"error": str(e)})


def _detect_logging_patterns(content: str) -> List[str]:
    """Detect logging patterns."""
    patterns = []
    if "structured logging" in content:
        patterns.append("Structured Logging")
    if "log level" in content:
        patterns.append("Log Levels")
    if "log rotation" in content:
        patterns.append("Log Rotation")
    return patterns


def _detect_security_patterns(content: str) -> List[str]:
    """Detect security patterns."""
    patterns = []
    if "jwt" in content:
        patterns.append("JWT Authentication")
    if "oauth" in content:
        patterns.append("OAuth")
    if "bcrypt" in content or "hash" in content:
        patterns.append("Password Hashing")
    if "cors" in content:
        patterns.append("CORS")
    return patterns


def _detect_caching_patterns(content: str) -> List[str]:
    """Detect caching patterns."""
    patterns = []
    if "redis" in content:
        patterns.append("Redis Cache")
    if "memcache" in content:
        patterns.append("Memcached")
    if "cache-aside" in content:
        patterns.append("Cache-Aside Pattern")
    return patterns


def _detect_monitoring_patterns(content: str) -> List[str]:
    """Detect monitoring patterns."""
    patterns = []
    if "prometheus" in content:
        patterns.append("Prometheus Metrics")
    if "grafana" in content:
        patterns.append("Grafana Dashboard")
    if "jaeger" in content or "zipkin" in content:
        patterns.append("Distributed Tracing")
    return patterns


def _detect_error_patterns(content: str) -> List[str]:
    """Detect error handling patterns."""
    patterns = []
    if "global error handler" in content:
        patterns.append("Global Error Handler")
    if "circuit breaker" in content:
        patterns.append("Circuit Breaker")
    if "retry" in content:
        patterns.append("Retry Pattern")
    return patterns


def _detect_config_patterns(content: str) -> List[str]:
    """Detect configuration patterns."""
    patterns = []
    if "environment variable" in content:
        patterns.append("Environment Variables")
    if "config file" in content:
        patterns.append("Configuration Files")
    if "feature flag" in content:
        patterns.append("Feature Flags")
    return patterns


@tool
def analyze_dependencies_and_relationships(files_data: str) -> str:
    """Analyze dependencies and relationships between files."""
    try:
        files = json.loads(files_data)
        relationships = {
            "imports": {},
            "dependencies": {},
            "circular_dependencies": [],
            "coupling_analysis": {}
        }
        
        for file_info in files:
            path = file_info.get("path", "")
            content = file_info.get("content", "")
            language = file_info.get("language", "")
            
            # Extract imports based on language
            imports = _extract_imports(content, language)
            relationships["imports"][path] = imports
            
            # Analyze coupling
            coupling_score = _calculate_coupling_score(content, imports)
            relationships["coupling_analysis"][path] = {
                "score": coupling_score,
                "level": _get_coupling_level(coupling_score)
            }
        
        # Detect circular dependencies
        relationships["circular_dependencies"] = _detect_circular_dependencies(relationships["imports"])
        
        return json.dumps(relationships, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        return json.dumps({"error": str(e)})


def _extract_imports(content: str, language: str) -> List[str]:
    """Extract imports from code content."""
    imports = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if language.lower() in ['python', 'py']:
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        elif language.lower() in ['javascript', 'js', 'typescript', 'ts']:
            if 'import ' in line or 'require(' in line:
                imports.append(line)
        elif language.lower() in ['java']:
            if line.startswith('import '):
                imports.append(line)
    
    return imports


def _calculate_coupling_score(content: str, imports: List[str]) -> float:
    """Calculate coupling score based on imports and content analysis."""
    # Simple heuristic: more imports = higher coupling
    base_score = len(imports) * 0.1
    
    # Additional factors
    if 'class ' in content:
        base_score += 0.2
    if 'interface ' in content:
        base_score += 0.1
    if 'extends ' in content or 'implements ' in content:
        base_score += 0.3
    
    return min(base_score, 1.0)  # Cap at 1.0


def _get_coupling_level(score: float) -> str:
    """Get coupling level based on score."""
    if score < 0.3:
        return "Low"
    elif score < 0.6:
        return "Medium"
    else:
        return "High"


def _detect_circular_dependencies(imports_map: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Detect circular dependencies in the import graph."""
    # Simplified circular dependency detection
    circular_deps = []
    
    for file_path, imports in imports_map.items():
        for import_line in imports:
            # Extract module name from import (simplified)
            module_name = _extract_module_name(import_line)
            if module_name and module_name in imports_map:
                # Check if the imported module imports back
                for reverse_import in imports_map[module_name]:
                    reverse_module = _extract_module_name(reverse_import)
                    if reverse_module and file_path.endswith(reverse_module):
                        circular_deps.append({
                            "file1": file_path,
                            "file2": module_name,
                            "type": "direct"
                        })
    
    return circular_deps


def _extract_module_name(import_line: str) -> Optional[str]:
    """Extract module name from import line."""
    # Simplified extraction
    if 'from ' in import_line:
        parts = import_line.split('from ')
        if len(parts) > 1:
            return parts[1].split()[0].strip()
    elif 'import ' in import_line:
        parts = import_line.split('import ')
        if len(parts) > 1:
            return parts[1].split()[0].strip()
    return None


class ContextAgent(BaseCodeMorphAgent):
    """Advanced Context Agent for building comprehensive project context."""
    
    def __init__(self, llm: Optional[ChatGroq] = None):
        """Initialize the Context Agent."""
        tools = [
            analyze_architecture_layers,
            detect_cross_cutting_concerns,
            analyze_dependencies_and_relationships
        ]
        super().__init__(
            name="Context Agent",
            description="Advanced context building and pattern detection agent",
            tools=tools,
            llm=llm
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the context agent."""
        return """You are an expert context analysis agent specializing in understanding software architecture and code organization.

Your capabilities include:
1. Architecture layer analysis and classification
2. Cross-cutting concerns detection
3. Dependency relationship mapping
4. Pattern recognition across the codebase
5. Component interaction analysis

When analyzing context, you should:
- Identify architectural layers and their responsibilities
- Detect cross-cutting concerns like logging, security, caching
- Map dependencies and relationships between components
- Recognize design patterns and architectural styles
- Assess coupling and cohesion levels
- Provide insights for architectural improvements

Always structure your analysis with:
- Architecture overview and layer identification
- Cross-cutting concerns summary
- Dependency analysis and coupling metrics
- Pattern recognition results
- Architectural recommendations

Focus on providing a clear understanding of the codebase structure and organization."""
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Get default tools for the context agent."""
        return [
            analyze_architecture_layers,
            detect_cross_cutting_concerns,
            analyze_dependencies_and_relationships
        ]
    
    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data for the context agent."""
        files = input_data.get("files", [])
        parse_results = input_data.get("parse_results", [])
        
        prompt = f"""Analyze the following codebase for architectural context and organization:

Total Files: {len(files)}
Parsed Results Available: {len(parse_results)}

Files Overview:
"""
        
        for i, file_info in enumerate(files[:5]):  # Limit to first 5 files for prompt
            prompt += f"""
File {i+1}: {file_info.get('path', 'unknown')}
- Type: {file_info.get('type', 'unknown')}
- Size: {file_info.get('size', len(file_info.get('content', '')))} chars
"""
            
            # Include code content for analysis
            content = file_info.get('content', '')
            if content and len(content) < 1000:
                prompt += f"Content:\n```\n{content[:800]}...\n```\n"
        
        if len(files) > 5:
            prompt += f"\n... and {len(files) - 5} more files"
        
        prompt += """

Please analyze the codebase context focusing on:
1. Architecture layers and component organization
2. Cross-cutting concerns (logging, security, caching, etc.)
3. Dependencies and relationships between components
4. Design patterns and architectural styles
5. Code organization and structure quality

Provide a comprehensive context analysis with confidence scores."""
        
        return prompt
    
    async def analyze(self, input_data: ContextAnalysisInput) -> AgentResult:
        """Perform comprehensive context analysis."""
        try:
            logger.info("Starting context analysis")
            
            # Prepare files data for tools
            files_json = json.dumps(input_data.files)
            
            # Run all analysis tools
            architecture_analysis = analyze_architecture_layers.invoke({"files_data": files_json})
            concerns_analysis = detect_cross_cutting_concerns.invoke({"files_data": files_json})
            dependencies_analysis = analyze_dependencies_and_relationships.invoke({"files_data": files_json})
            
            # Combine results
            context_data = {
                "architecture_layers": json.loads(architecture_analysis),
                "cross_cutting_concerns": json.loads(concerns_analysis),
                "dependencies_and_relationships": json.loads(dependencies_analysis),
                "project_info": input_data.project_info,
                "summary": self._generate_context_summary(
                    json.loads(architecture_analysis),
                    json.loads(concerns_analysis),
                    json.loads(dependencies_analysis)
                )
            }
            
            return AgentResult(
                success=True,
                data=context_data,
                confidence=0.9,
                reasoning="Context analysis completed successfully",
                errors=[],
                metadata={"agent": "ContextAgent", "analysis_type": "context"}
            )
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                reasoning=f"Context analysis failed: {str(e)}",
                errors=[str(e)],
                metadata={"agent": "ContextAgent", "error": True}
            )
    
    def _generate_context_summary(self, architecture: Dict, concerns: Dict, dependencies: Dict) -> Dict[str, Any]:
        """Generate a summary of the context analysis."""
        summary = {
            "total_files_analyzed": sum(len(layer["files"]) for layer in architecture.values()),
            "architecture_layers": {
                layer: len(data["files"]) 
                for layer, data in architecture.items()
            },
            "cross_cutting_concerns": {
                concern: len(data["files"]) 
                for concern, data in concerns.items()
            },
            "dependency_insights": {
                "total_files_with_imports": len(dependencies.get("imports", {})),
                "circular_dependencies_count": len(dependencies.get("circular_dependencies", [])),
                "high_coupling_files": len([
                    f for f, data in dependencies.get("coupling_analysis", {}).items()
                    if data.get("level") == "High"
                ])
            },
            "recommendations": self._generate_recommendations(architecture, concerns, dependencies)
        }
        
        return summary
    
    def _generate_recommendations(self, architecture: Dict, concerns: Dict, dependencies: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Architecture recommendations
        if len(architecture.get("presentation", {}).get("files", [])) == 0:
            recommendations.append("Consider adding a presentation layer for better separation of concerns")
        
        # Cross-cutting concerns recommendations
        if len(concerns.get("logging", {}).get("files", [])) < 3:
            recommendations.append("Consider implementing consistent logging across more components")
        
        if len(concerns.get("security", {}).get("files", [])) == 0:
            recommendations.append("Consider implementing security measures and authentication")
        
        # Dependency recommendations
        circular_deps = dependencies.get("circular_dependencies", [])
        if len(circular_deps) > 0:
            recommendations.append(f"Found {len(circular_deps)} circular dependencies that should be resolved")
        
        high_coupling_files = [
            f for f, data in dependencies.get("coupling_analysis", {}).items()
            if data.get("level") == "High"
        ]
        if len(high_coupling_files) > 0:
            recommendations.append(f"Consider refactoring {len(high_coupling_files)} files with high coupling")
        
        return recommendations
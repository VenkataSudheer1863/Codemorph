"""Enhanced Dependency Graph Analysis Tools."""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    id: str
    name: str
    type: str  # file, class, function, module
    file_path: str
    language: str
    metadata: Dict[str, Any]


@dataclass
class DependencyEdge:
    """Represents an edge in the dependency graph."""
    source: str
    target: str
    type: str  # import, call, inheritance, composition
    weight: float
    metadata: Dict[str, Any]


class DependencyGraphInput(BaseModel):
    """Input for dependency graph analysis."""
    files: List[Dict[str, Any]] = Field(description="List of file data with content")
    parse_results: List[Dict[str, Any]] = Field(description="Parsed code results")


class EnhancedDependencyGraphTool(BaseTool):
    """Enhanced tool for building comprehensive dependency graphs."""
    
    name: str = "enhanced_dependency_graph"
    description: str = "Build comprehensive dependency graphs with advanced analysis"
    
    def _run(self, files_data: str) -> str:
        """Build enhanced dependency graph from files data."""
        try:
            data = json.loads(files_data)
            files = data.get("files", [])
            parse_results = data.get("parse_results", [])
            
            # Build the dependency graph
            graph = self._build_dependency_graph(files, parse_results)
            
            # Analyze the graph
            analysis = self._analyze_dependency_graph(graph)
            
            return json.dumps({
                "graph": graph,
                "analysis": analysis,
                "success": True
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Enhanced dependency graph analysis failed: {e}")
            return json.dumps({
                "error": str(e),
                "success": False
            })
    
    def _build_dependency_graph(
        self,
        files: List[Dict[str, Any]],
        parse_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build comprehensive dependency graph."""
        nodes = {}
        edges = []
        
        # Create nodes for files, classes, and functions
        for i, file_info in enumerate(files):
            file_path = file_info.get("path", f"file_{i}")
            language = file_info.get("language", "unknown")
            content = file_info.get("content", "")
            
            # File node
            file_node = DependencyNode(
                id=f"file:{file_path}",
                name=file_path.split("/")[-1],
                type="file",
                file_path=file_path,
                language=language,
                metadata={
                    "size": len(content),
                    "lines": len(content.split('\n')),
                    "extension": file_path.split('.')[-1] if '.' in file_path else ""
                }
            )
            nodes[file_node.id] = file_node.__dict__
            
            # Extract classes and functions from parse results
            if i < len(parse_results):
                parse_result = parse_results[i]
                
                # Class nodes
                for cls in parse_result.get("classes", []):
                    class_node = DependencyNode(
                        id=f"class:{file_path}:{cls['name']}",
                        name=cls["name"],
                        type="class",
                        file_path=file_path,
                        language=language,
                        metadata={
                            "methods": len(cls.get("methods", [])),
                            "parent_classes": cls.get("parent_classes", []),
                            "interfaces": cls.get("interfaces", [])
                        }
                    )
                    nodes[class_node.id] = class_node.__dict__
                    
                    # Edge from file to class
                    edges.append(DependencyEdge(
                        source=file_node.id,
                        target=class_node.id,
                        type="contains",
                        weight=1.0,
                        metadata={}
                    ).__dict__)
                
                # Function nodes
                for func in parse_result.get("functions", []):
                    func_node = DependencyNode(
                        id=f"function:{file_path}:{func['name']}",
                        name=func["name"],
                        type="function",
                        file_path=file_path,
                        language=language,
                        metadata={
                            "parameters": len(func.get("parameters", [])),
                            "return_type": func.get("return_type", "unknown"),
                            "complexity": func.get("complexity", 1)
                        }
                    )
                    nodes[func_node.id] = func_node.__dict__
                    
                    # Edge from file to function
                    edges.append(DependencyEdge(
                        source=file_node.id,
                        target=func_node.id,
                        type="contains",
                        weight=1.0,
                        metadata={}
                    ).__dict__)
        
        # Create dependency edges
        for i, file_info in enumerate(files):
            if i < len(parse_results):
                parse_result = parse_results[i]
                file_path = file_info.get("path", f"file_{i}")
                
                # Import dependencies
                for imp in parse_result.get("imports", []):
                    target_file = self._resolve_import_to_file(imp, files)
                    if target_file:
                        edges.append(DependencyEdge(
                            source=f"file:{file_path}",
                            target=f"file:{target_file}",
                            type="import",
                            weight=0.5,
                            metadata={"import_statement": imp}
                        ).__dict__)
                
                # Function call dependencies
                for call in parse_result.get("function_calls", []):
                    # Try to resolve function calls to actual functions
                    target_func = self._resolve_function_call(call, nodes)
                    if target_func:
                        source_func = f"function:{file_path}:{call.get('caller', 'unknown')}"
                        if source_func in nodes:
                            edges.append(DependencyEdge(
                                source=source_func,
                                target=target_func,
                                type="call",
                                weight=1.0,
                                metadata={"call_type": call.get("type", "direct")}
                            ).__dict__)
                
                # Inheritance dependencies
                for cls in parse_result.get("classes", []):
                    for parent in cls.get("parent_classes", []):
                        parent_class = self._resolve_class_reference(parent, nodes)
                        if parent_class:
                            edges.append(DependencyEdge(
                                source=f"class:{file_path}:{cls['name']}",
                                target=parent_class,
                                type="inheritance",
                                weight=2.0,
                                metadata={"inheritance_type": "extends"}
                            ).__dict__)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def _analyze_dependency_graph(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the dependency graph for insights."""
        nodes = graph["nodes"]
        edges = graph["edges"]
        
        analysis = {
            "metrics": self._calculate_graph_metrics(nodes, edges),
            "cycles": self._detect_cycles(nodes, edges),
            "clusters": self._detect_clusters(nodes, edges),
            "critical_paths": self._find_critical_paths(nodes, edges),
            "hotspots": self._identify_hotspots(nodes, edges),
            "architectural_violations": self._detect_architectural_violations(nodes, edges)
        }
        
        return analysis
    
    def _calculate_graph_metrics(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate various graph metrics."""
        # Build adjacency lists
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in edges:
            out_degree[edge["source"]] += 1
            in_degree[edge["target"]] += 1
        
        # Calculate metrics
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        # Density
        max_edges = total_nodes * (total_nodes - 1)
        density = total_edges / max_edges if max_edges > 0 else 0
        
        # Average degree
        avg_in_degree = sum(in_degree.values()) / total_nodes if total_nodes > 0 else 0
        avg_out_degree = sum(out_degree.values()) / total_nodes if total_nodes > 0 else 0
        
        # Find nodes with highest degrees
        max_in_degree = max(in_degree.values()) if in_degree else 0
        max_out_degree = max(out_degree.values()) if out_degree else 0
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "density": density,
            "average_in_degree": avg_in_degree,
            "average_out_degree": avg_out_degree,
            "max_in_degree": max_in_degree,
            "max_out_degree": max_out_degree,
            "complexity_score": self._calculate_complexity_score(density, avg_in_degree, avg_out_degree)
        }
    
    def _detect_cycles(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect circular dependencies."""
        # Build adjacency list
        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])
        
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append({
                    "cycle": cycle,
                    "length": len(cycle) - 1,
                    "type": self._classify_cycle_type(cycle, nodes)
                })
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path[:])
            
            rec_stack.remove(node)
        
        for node in nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _detect_clusters(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect clusters of highly connected components."""
        # Use simple connected components algorithm
        graph = defaultdict(set)
        for edge in edges:
            graph[edge["source"]].add(edge["target"])
            graph[edge["target"]].add(edge["source"])
        
        visited = set()
        clusters = []
        
        def dfs(node, cluster):
            if node in visited:
                return
            visited.add(node)
            cluster.append(node)
            for neighbor in graph[node]:
                dfs(neighbor, cluster)
        
        for node in nodes:
            if node not in visited:
                cluster = []
                dfs(node, cluster)
                if len(cluster) > 1:
                    clusters.append({
                        "nodes": cluster,
                        "size": len(cluster),
                        "cohesion": self._calculate_cluster_cohesion(cluster, edges)
                    })
        
        return sorted(clusters, key=lambda x: x["size"], reverse=True)
    
    def _find_critical_paths(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find critical paths in the dependency graph."""
        # Simplified critical path analysis
        critical_paths = []
        
        # Find entry points (nodes with no incoming edges)
        incoming = defaultdict(int)
        for edge in edges:
            incoming[edge["target"]] += 1
        
        entry_points = [node for node in nodes if incoming[node] == 0]
        
        # For each entry point, find longest paths
        for entry in entry_points[:5]:  # Limit to top 5 entry points
            path = self._find_longest_path_from(entry, nodes, edges)
            if len(path) > 2:
                critical_paths.append({
                    "path": path,
                    "length": len(path),
                    "entry_point": entry,
                    "impact_score": self._calculate_path_impact(path, nodes, edges)
                })
        
        return sorted(critical_paths, key=lambda x: x["impact_score"], reverse=True)
    
    def _identify_hotspots(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify dependency hotspots."""
        # Calculate centrality measures
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in edges:
            out_degree[edge["source"]] += 1
            in_degree[edge["target"]] += 1
        
        hotspots = []
        for node_id, node_data in nodes.items():
            hotspot_score = (in_degree[node_id] * 2 + out_degree[node_id]) / 3
            if hotspot_score > 2:  # Threshold for hotspot
                hotspots.append({
                    "node": node_id,
                    "name": node_data["name"],
                    "type": node_data["type"],
                    "in_degree": in_degree[node_id],
                    "out_degree": out_degree[node_id],
                    "hotspot_score": hotspot_score,
                    "risk_level": self._calculate_risk_level(hotspot_score)
                })
        
        return sorted(hotspots, key=lambda x: x["hotspot_score"], reverse=True)
    
    def _detect_architectural_violations(
        self,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect architectural violations in dependencies."""
        violations = []
        
        # Define architectural layers
        layers = {
            "presentation": ["ui", "view", "controller", "frontend"],
            "business": ["service", "logic", "domain", "business"],
            "data": ["repository", "dao", "model", "entity", "database"],
            "infrastructure": ["config", "util", "helper", "infrastructure"]
        }
        
        # Classify nodes into layers
        node_layers = {}
        for node_id, node_data in nodes.items():
            file_path = node_data["file_path"].lower()
            node_layer = "unknown"
            
            for layer, keywords in layers.items():
                if any(keyword in file_path for keyword in keywords):
                    node_layer = layer
                    break
            
            node_layers[node_id] = node_layer
        
        # Check for layer violations
        layer_hierarchy = ["presentation", "business", "data", "infrastructure"]
        
        for edge in edges:
            source_layer = node_layers.get(edge["source"], "unknown")
            target_layer = node_layers.get(edge["target"], "unknown")
            
            if source_layer != "unknown" and target_layer != "unknown":
                source_level = layer_hierarchy.index(source_layer) if source_layer in layer_hierarchy else -1
                target_level = layer_hierarchy.index(target_layer) if target_layer in layer_hierarchy else -1
                
                # Violation: higher layer depending on lower layer (skip by more than 1)
                if source_level >= 0 and target_level >= 0 and source_level > target_level + 1:
                    violations.append({
                        "type": "layer_violation",
                        "source": edge["source"],
                        "target": edge["target"],
                        "source_layer": source_layer,
                        "target_layer": target_layer,
                        "severity": "high" if source_level - target_level > 2 else "medium",
                        "description": f"{source_layer} layer should not directly depend on {target_layer} layer"
                    })
        
        return violations
    
    def _resolve_import_to_file(self, import_stmt: str, files: List[Dict[str, Any]]) -> Optional[str]:
        """Resolve import statement to actual file path."""
        # Simplified import resolution
        for file_info in files:
            file_path = file_info.get("path", "")
            if import_stmt.lower() in file_path.lower():
                return file_path
        return None
    
    def _resolve_function_call(self, call: Dict[str, Any], nodes: Dict[str, Any]) -> Optional[str]:
        """Resolve function call to actual function node."""
        call_name = call.get("name", "")
        for node_id, node_data in nodes.items():
            if node_data["type"] == "function" and node_data["name"] == call_name:
                return node_id
        return None
    
    def _resolve_class_reference(self, class_name: str, nodes: Dict[str, Any]) -> Optional[str]:
        """Resolve class reference to actual class node."""
        for node_id, node_data in nodes.items():
            if node_data["type"] == "class" and node_data["name"] == class_name:
                return node_id
        return None
    
    def _classify_cycle_type(self, cycle: List[str], nodes: Dict[str, Any]) -> str:
        """Classify the type of cycle."""
        node_types = [nodes[node]["type"] for node in cycle[:-1]]
        
        if all(t == "file" for t in node_types):
            return "file_cycle"
        elif all(t == "class" for t in node_types):
            return "class_cycle"
        elif all(t == "function" for t in node_types):
            return "function_cycle"
        else:
            return "mixed_cycle"
    
    def _calculate_cluster_cohesion(self, cluster: List[str], edges: List[Dict[str, Any]]) -> float:
        """Calculate cohesion score for a cluster."""
        cluster_set = set(cluster)
        internal_edges = sum(1 for edge in edges 
                           if edge["source"] in cluster_set and edge["target"] in cluster_set)
        max_internal_edges = len(cluster) * (len(cluster) - 1)
        return internal_edges / max_internal_edges if max_internal_edges > 0 else 0
    
    def _find_longest_path_from(
        self,
        start: str,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> List[str]:
        """Find longest path from a starting node."""
        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])
        
        def dfs(node, visited, path):
            if node in visited:
                return path
            
            visited.add(node)
            longest = path + [node]
            
            for neighbor in graph[node]:
                candidate = dfs(neighbor, visited.copy(), path + [node])
                if len(candidate) > len(longest):
                    longest = candidate
            
            return longest
        
        return dfs(start, set(), [])
    
    def _calculate_path_impact(
        self,
        path: List[str],
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]]
    ) -> float:
        """Calculate impact score for a path."""
        # Simple impact calculation based on path length and node types
        impact = len(path)
        for node in path:
            if node in nodes:
                node_type = nodes[node]["type"]
                if node_type == "file":
                    impact += 1
                elif node_type == "class":
                    impact += 2
                elif node_type == "function":
                    impact += 0.5
        return impact
    
    def _calculate_risk_level(self, hotspot_score: float) -> str:
        """Calculate risk level based on hotspot score."""
        if hotspot_score > 10:
            return "critical"
        elif hotspot_score > 5:
            return "high"
        elif hotspot_score > 2:
            return "medium"
        else:
            return "low"
    
    def _calculate_complexity_score(
        self,
        density: float,
        avg_in_degree: float,
        avg_out_degree: float
    ) -> float:
        """Calculate overall complexity score."""
        return (density * 0.4 + (avg_in_degree + avg_out_degree) * 0.3) * 10
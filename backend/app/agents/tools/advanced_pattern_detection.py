"""Advanced Pattern Detection Tools for CodeMorph."""

import logging
from typing import Any, Dict, List, Optional
import json
import re
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected pattern."""
    pattern_type: str
    pattern_name: str
    confidence: float
    location: Dict[str, Any]
    evidence: List[str]
    metadata: Dict[str, Any]


class AdvancedPatternDetectionInput(BaseModel):
    """Input for advanced pattern detection."""
    files: List[Dict[str, Any]] = Field(description="List of file data")
    context: Dict[str, Any] = Field(description="Analysis context")


class ArchitecturalPatternDetector(BaseTool):
    """Detects architectural patterns in codebases."""
    
    name: str = "architectural_pattern_detector"
    description: str = "Detect architectural patterns like MVC, MVP, MVVM, etc."
    
    def _run(self, files_data: str) -> str:
        """Detect architectural patterns."""
        try:
            data = json.loads(files_data)
            files = data.get("files", [])
            
            patterns = self._detect_architectural_patterns(files)
            
            return json.dumps({
                "patterns": [p.__dict__ for p in patterns],
                "summary": self._summarize_patterns(patterns),
                "success": True
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Architectural pattern detection failed: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    def _detect_architectural_patterns(self, files: List[Dict[str, Any]]) -> List[PatternMatch]:
        """Detect various architectural patterns."""
        patterns = []
        
        # MVC Pattern Detection
        mvc_evidence = self._detect_mvc_pattern(files)
        if mvc_evidence["confidence"] > 0.6:
            patterns.append(PatternMatch(
                pattern_type="architectural",
                pattern_name="Model-View-Controller (MVC)",
                confidence=mvc_evidence["confidence"],
                location=mvc_evidence["location"],
                evidence=mvc_evidence["evidence"],
                metadata=mvc_evidence["metadata"]
            ))
        
        # Microservices Pattern Detection
        microservices_evidence = self._detect_microservices_pattern(files)
        if microservices_evidence["confidence"] > 0.5:
            patterns.append(PatternMatch(
                pattern_type="architectural",
                pattern_name="Microservices",
                confidence=microservices_evidence["confidence"],
                location=microservices_evidence["location"],
                evidence=microservices_evidence["evidence"],
                metadata=microservices_evidence["metadata"]
            ))
        
        return patterns
    
    def _detect_mvc_pattern(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect MVC pattern implementation."""
        evidence = []
        confidence = 0.0
        location = {}
        metadata = {}
        
        model_files = []
        view_files = []
        controller_files = []
        
        for file_info in files:
            path = file_info.get("path", "").lower()
            content = file_info.get("content", "").lower()
            
            # Model detection
            if any(keyword in path for keyword in ["model", "entity", "domain"]):
                model_files.append(file_info["path"])
                evidence.append(f"Model component found: {file_info['path']}")
            
            # View detection
            if any(keyword in path for keyword in ["view", "template", "ui", "frontend"]):
                view_files.append(file_info["path"])
                evidence.append(f"View component found: {file_info['path']}")
            
            # Controller detection
            if any(keyword in path for keyword in ["controller", "handler", "resource"]):
                controller_files.append(file_info["path"])
                evidence.append(f"Controller component found: {file_info['path']}")
        
        # Calculate confidence based on presence of all three components
        components_found = sum([len(model_files) > 0, len(view_files) > 0, len(controller_files) > 0])
        confidence = components_found / 3.0
        
        location = {
            "models": model_files,
            "views": view_files,
            "controllers": controller_files
        }
        
        metadata = {
            "model_count": len(model_files),
            "view_count": len(view_files),
            "controller_count": len(controller_files),
            "separation_score": self._calculate_separation_score(model_files, view_files, controller_files)
        }
        
        return {
            "confidence": confidence,
            "evidence": evidence,
            "location": location,
            "metadata": metadata
        }
    
    def _detect_microservices_pattern(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect microservices architecture pattern."""
        evidence = []
        confidence = 0.0
        location = {}
        metadata = {}
        
        service_indicators = []
        api_gateways = []
        config_files = []
        
        for file_info in files:
            path = file_info.get("path", "").lower()
            content = file_info.get("content", "").lower()
            
            # Service detection
            if "service" in path and any(ext in path for ext in [".py", ".java", ".js", ".go"]):
                service_indicators.append(file_info["path"])
                evidence.append(f"Service component: {file_info['path']}")
            
            # API Gateway detection
            if any(keyword in content for keyword in ["gateway", "proxy", "load balancer"]):
                api_gateways.append(file_info["path"])
                evidence.append(f"API Gateway indicator: {file_info['path']}")
            
            # Configuration files
            if any(keyword in path for keyword in ["docker", "k8s", "kubernetes", "compose"]):
                config_files.append(file_info["path"])
                evidence.append(f"Deployment config: {file_info['path']}")
        
        # Calculate confidence
        if len(service_indicators) > 1:
            confidence += 0.4
        if len(api_gateways) > 0:
            confidence += 0.3
        if len(config_files) > 0:
            confidence += 0.3
        
        location = {
            "services": service_indicators,
            "gateways": api_gateways,
            "configs": config_files
        }
        
        metadata = {
            "service_count": len(service_indicators),
            "has_gateway": len(api_gateways) > 0,
            "deployment_ready": len(config_files) > 0
        }
        
        return {
            "confidence": min(confidence, 1.0),
            "evidence": evidence,
            "location": location,
            "metadata": metadata
        }
    
    def _calculate_separation_score(self, models: List[str], views: List[str], controllers: List[str]) -> float:
        """Calculate how well separated the MVC components are."""
        # Simple heuristic: check if components are in separate directories
        model_dirs = set(path.split('/')[:-1] for path in models if '/' in path)
        view_dirs = set(path.split('/')[:-1] for path in views if '/' in path)
        controller_dirs = set(path.split('/')[:-1] for path in controllers if '/' in path)
        
        total_dirs = len(model_dirs | view_dirs | controller_dirs)
        if total_dirs == 0:
            return 0.0
        
        # Higher score if components are in different directories
        separation_score = len(model_dirs) + len(view_dirs) + len(controller_dirs)
        return min(separation_score / (total_dirs * 3), 1.0)
    
    def _summarize_patterns(self, patterns: List[PatternMatch]) -> Dict[str, Any]:
        """Summarize detected patterns."""
        return {
            "total_patterns": len(patterns),
            "high_confidence": len([p for p in patterns if p.confidence > 0.8]),
            "medium_confidence": len([p for p in patterns if 0.5 < p.confidence <= 0.8]),
            "low_confidence": len([p for p in patterns if p.confidence <= 0.5]),
            "pattern_types": list(set(p.pattern_type for p in patterns)),
            "most_confident": max(patterns, key=lambda p: p.confidence).pattern_name if patterns else None
        }


class DesignPatternDetector(BaseTool):
    """Detects design patterns in code."""
    
    name: str = "design_pattern_detector"
    description: str = "Detect design patterns like Singleton, Factory, Observer, etc."
    
    def _run(self, files_data: str) -> str:
        """Detect design patterns."""
        try:
            data = json.loads(files_data)
            files = data.get("files", [])
            
            patterns = self._detect_design_patterns(files)
            
            return json.dumps({
                "patterns": [p.__dict__ for p in patterns],
                "summary": self._summarize_patterns(patterns),
                "success": True
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Design pattern detection failed: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    def _detect_design_patterns(self, files: List[Dict[str, Any]]) -> List[PatternMatch]:
        """Detect various design patterns."""
        patterns = []
        
        for file_info in files:
            content = file_info.get("content", "")
            path = file_info.get("path", "")
            
            # Singleton Pattern
            singleton_match = self._detect_singleton_pattern(content, path)
            if singleton_match:
                patterns.append(singleton_match)
            
            # Factory Pattern
            factory_match = self._detect_factory_pattern(content, path)
            if factory_match:
                patterns.append(factory_match)
            
            # Observer Pattern
            observer_match = self._detect_observer_pattern(content, path)
            if observer_match:
                patterns.append(observer_match)
        
        return patterns
    
    def _detect_singleton_pattern(self, content: str, path: str) -> Optional[PatternMatch]:
        """Detect Singleton pattern."""
        evidence = []
        confidence = 0.0
        
        # Look for singleton indicators
        if re.search(r'private\s+static\s+\w+\s+instance', content, re.IGNORECASE):
            evidence.append("Private static instance variable found")
            confidence += 0.4
        
        if re.search(r'private\s+\w+\s*\(', content, re.IGNORECASE):
            evidence.append("Private constructor found")
            confidence += 0.3
        
        if re.search(r'getInstance\s*\(', content, re.IGNORECASE):
            evidence.append("getInstance method found")
            confidence += 0.3
        
        if confidence > 0.5:
            return PatternMatch(
                pattern_type="design",
                pattern_name="Singleton",
                confidence=confidence,
                location={"file": path},
                evidence=evidence,
                metadata={"implementation_type": "classic"}
            )
        
        return None
    
    def _detect_factory_pattern(self, content: str, path: str) -> Optional[PatternMatch]:
        """Detect Factory pattern."""
        evidence = []
        confidence = 0.0
        
        # Look for factory indicators
        if re.search(r'create\w*\s*\(', content, re.IGNORECASE):
            evidence.append("Create method found")
            confidence += 0.3
        
        if "factory" in path.lower() or "factory" in content.lower():
            evidence.append("Factory naming convention")
            confidence += 0.4
        
        if re.search(r'new\s+\w+\s*\(', content) and re.search(r'return\s+\w+', content):
            evidence.append("Object creation and return pattern")
            confidence += 0.3
        
        if confidence > 0.5:
            return PatternMatch(
                pattern_type="design",
                pattern_name="Factory",
                confidence=confidence,
                location={"file": path},
                evidence=evidence,
                metadata={"factory_type": "simple"}
            )
        
        return None
    
    def _detect_observer_pattern(self, content: str, path: str) -> Optional[PatternMatch]:
        """Detect Observer pattern."""
        evidence = []
        confidence = 0.0
        
        # Look for observer indicators
        if re.search(r'addObserver|subscribe|addEventListener', content, re.IGNORECASE):
            evidence.append("Observer registration method found")
            confidence += 0.4
        
        if re.search(r'notify|publish|fire|trigger', content, re.IGNORECASE):
            evidence.append("Notification method found")
            confidence += 0.4
        
        if re.search(r'Observer|Listener|Subscriber', content):
            evidence.append("Observer interface/class found")
            confidence += 0.2
        
        if confidence > 0.5:
            return PatternMatch(
                pattern_type="design",
                pattern_name="Observer",
                confidence=confidence,
                location={"file": path},
                evidence=evidence,
                metadata={"observer_type": "classic"}
            )
        
        return None
    
    def _summarize_patterns(self, patterns: List[PatternMatch]) -> Dict[str, Any]:
        """Summarize detected patterns."""
        return {
            "total_patterns": len(patterns),
            "pattern_distribution": {
                pattern.pattern_name: len([p for p in patterns if p.pattern_name == pattern.pattern_name])
                for pattern in patterns
            },
            "average_confidence": sum(p.confidence for p in patterns) / len(patterns) if patterns else 0,
            "files_with_patterns": len(set(p.location.get("file") for p in patterns if "file" in p.location))
        }
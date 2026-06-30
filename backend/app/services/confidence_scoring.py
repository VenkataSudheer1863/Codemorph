"""Comprehensive Confidence Scoring System for CodeMorph."""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class ConfidenceCategory(Enum):
    """Categories for confidence scoring."""
    PARSING = "parsing"
    ANALYSIS = "analysis"
    PATTERN_DETECTION = "pattern_detection"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    DEPENDENCIES = "dependencies"
    RECOMMENDATIONS = "recommendations"
    OVERALL = "overall"


@dataclass
class ConfidenceScore:
    """Represents a confidence score with metadata."""
    category: ConfidenceCategory
    score: float  # 0.0 to 1.0
    reasoning: str
    evidence: List[str]
    factors: Dict[str, float]
    metadata: Dict[str, Any]


class ConfidenceScoringEngine:
    """Engine for calculating comprehensive confidence scores."""
    
    def __init__(self):
        self.category_weights = {
            ConfidenceCategory.PARSING: 0.15,
            ConfidenceCategory.ANALYSIS: 0.20,
            ConfidenceCategory.PATTERN_DETECTION: 0.15,
            ConfidenceCategory.ARCHITECTURE: 0.15,
            ConfidenceCategory.SECURITY: 0.10,
            ConfidenceCategory.DEPENDENCIES: 0.15,
            ConfidenceCategory.RECOMMENDATIONS: 0.10
        }
    
    def calculate_comprehensive_confidence(
        self,
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any],
        files: List[Dict[str, Any]],
        errors: List[str]
    ) -> Dict[str, ConfidenceScore]:
        """Calculate comprehensive confidence scores across all categories."""
        confidence_scores = {}
        
        # Calculate individual category scores
        confidence_scores[ConfidenceCategory.PARSING] = self._calculate_parsing_confidence(
            files, errors
        )
        
        confidence_scores[ConfidenceCategory.ANALYSIS] = self._calculate_analysis_confidence(
            analysis_results, errors
        )
        
        confidence_scores[ConfidenceCategory.PATTERN_DETECTION] = self._calculate_pattern_confidence(
            analysis_results, context_results
        )
        
        confidence_scores[ConfidenceCategory.ARCHITECTURE] = self._calculate_architecture_confidence(
            context_results, analysis_results
        )
        
        confidence_scores[ConfidenceCategory.SECURITY] = self._calculate_security_confidence(
            analysis_results
        )
        
        confidence_scores[ConfidenceCategory.DEPENDENCIES] = self._calculate_dependency_confidence(
            context_results, analysis_results
        )
        
        confidence_scores[ConfidenceCategory.RECOMMENDATIONS] = self._calculate_recommendation_confidence(
            analysis_results, context_results, confidence_scores
        )
        
        # Calculate overall confidence
        confidence_scores[ConfidenceCategory.OVERALL] = self._calculate_overall_confidence(
            confidence_scores
        )
        
        return confidence_scores
    
    def _calculate_parsing_confidence(
        self,
        files: List[Dict[str, Any]],
        errors: List[str]
    ) -> ConfidenceScore:
        """Calculate confidence in parsing results."""
        evidence = []
        factors = {}
        
        total_files = len(files)
        if total_files == 0:
            return ConfidenceScore(
                category=ConfidenceCategory.PARSING,
                score=0.0,
                reasoning="No files to parse",
                evidence=["No input files provided"],
                factors={"file_count": 0.0},
                metadata={"total_files": 0}
            )
        
        # Factor 1: File processing success rate
        parsing_errors = [e for e in errors if "parse" in e.lower() or "syntax" in e.lower()]
        success_rate = max(0.0, (total_files - len(parsing_errors)) / total_files)
        factors["success_rate"] = success_rate
        evidence.append(f"Successfully processed {total_files - len(parsing_errors)}/{total_files} files")
        
        # Factor 2: Language support coverage
        languages = [f.get("language", "unknown") for f in files]
        supported_languages = ["python", "java", "javascript", "typescript", "c", "cpp", "go", "rust"]
        supported_count = sum(1 for lang in languages if lang.lower() in supported_languages)
        language_coverage = supported_count / total_files if total_files > 0 else 0.0
        factors["language_coverage"] = language_coverage
        evidence.append(f"Language support coverage: {language_coverage:.1%}")
        
        # Factor 3: File size distribution
        file_sizes = [f.get("size", 0) for f in files]
        avg_size = statistics.mean(file_sizes) if file_sizes else 0
        size_factor = min(1.0, avg_size / 10000)  # Normalize to reasonable file size
        factors["size_factor"] = size_factor
        evidence.append(f"Average file size: {avg_size:.0f} bytes")
        
        # Factor 4: Content quality
        content_quality = self._assess_content_quality(files)
        factors["content_quality"] = content_quality
        evidence.append(f"Content quality score: {content_quality:.2f}")
        
        # Calculate weighted score
        score = (
            success_rate * 0.4 +
            language_coverage * 0.3 +
            size_factor * 0.2 +
            content_quality * 0.1
        )
        
        reasoning = f"Parsing confidence based on {success_rate:.1%} success rate, {language_coverage:.1%} language coverage"
        
        return ConfidenceScore(
            category=ConfidenceCategory.PARSING,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "total_files": total_files,
                "parsing_errors": len(parsing_errors),
                "supported_languages": supported_count
            }
        )
    
    def _calculate_analysis_confidence(
        self,
        analysis_results: Dict[str, Any],
        errors: List[str]
    ) -> ConfidenceScore:
        """Calculate confidence in analysis results."""
        evidence = []
        factors = {}
        
        # Factor 1: Analysis completeness
        expected_components = ["complexity", "patterns", "security", "dependencies"]
        found_components = [comp for comp in expected_components if comp in analysis_results]
        completeness = len(found_components) / len(expected_components)
        factors["completeness"] = completeness
        evidence.append(f"Analysis completeness: {completeness:.1%}")
        
        # Factor 2: Analysis depth
        depth_indicators = 0
        if "detailed_metrics" in analysis_results:
            depth_indicators += 1
        if "code_quality_score" in analysis_results:
            depth_indicators += 1
        if "architectural_insights" in analysis_results:
            depth_indicators += 1
        
        depth_score = depth_indicators / 3.0
        factors["depth"] = depth_score
        evidence.append(f"Analysis depth score: {depth_score:.2f}")
        
        # Factor 3: Error rate
        analysis_errors = [e for e in errors if "analysis" in e.lower()]
        error_factor = max(0.0, 1.0 - len(analysis_errors) * 0.2)
        factors["error_factor"] = error_factor
        evidence.append(f"Analysis errors: {len(analysis_errors)}")
        
        # Factor 4: Result consistency
        consistency_score = self._assess_result_consistency(analysis_results)
        factors["consistency"] = consistency_score
        evidence.append(f"Result consistency: {consistency_score:.2f}")
        
        # Calculate weighted score
        score = (
            completeness * 0.3 +
            depth_score * 0.3 +
            error_factor * 0.2 +
            consistency_score * 0.2
        )
        
        reasoning = f"Analysis confidence based on {completeness:.1%} completeness and {depth_score:.2f} depth score"
        
        return ConfidenceScore(
            category=ConfidenceCategory.ANALYSIS,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "components_found": len(found_components),
                "analysis_errors": len(analysis_errors)
            }
        )
    
    def _calculate_pattern_confidence(
        self,
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any]
    ) -> ConfidenceScore:
        """Calculate confidence in pattern detection."""
        evidence = []
        factors = {}
        
        # Factor 1: Pattern detection coverage
        detected_patterns = []
        if "patterns" in analysis_results:
            detected_patterns.extend(analysis_results["patterns"])
        if "architectural_patterns" in context_results:
            detected_patterns.extend(context_results["architectural_patterns"])
        
        pattern_count = len(detected_patterns)
        coverage_score = min(1.0, pattern_count / 5.0)  # Normalize to 5 patterns
        factors["coverage"] = coverage_score
        evidence.append(f"Detected {pattern_count} patterns")
        
        # Factor 2: Pattern confidence scores
        if detected_patterns:
            pattern_confidences = [p.get("confidence", 0.5) for p in detected_patterns if isinstance(p, dict)]
            if pattern_confidences:
                avg_pattern_confidence = statistics.mean(pattern_confidences)
                factors["pattern_confidence"] = avg_pattern_confidence
                evidence.append(f"Average pattern confidence: {avg_pattern_confidence:.2f}")
            else:
                factors["pattern_confidence"] = 0.5
        else:
            factors["pattern_confidence"] = 0.0
        
        # Factor 3: Pattern diversity
        pattern_types = set()
        for pattern in detected_patterns:
            if isinstance(pattern, dict):
                pattern_types.add(pattern.get("type", "unknown"))
        
        diversity_score = min(1.0, len(pattern_types) / 3.0)  # Normalize to 3 types
        factors["diversity"] = diversity_score
        evidence.append(f"Pattern type diversity: {len(pattern_types)} types")
        
        # Calculate weighted score
        score = (
            coverage_score * 0.4 +
            factors.get("pattern_confidence", 0.0) * 0.4 +
            diversity_score * 0.2
        )
        
        reasoning = f"Pattern detection confidence based on {pattern_count} patterns with {factors.get('pattern_confidence', 0.0):.2f} avg confidence"
        
        return ConfidenceScore(
            category=ConfidenceCategory.PATTERN_DETECTION,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "pattern_count": pattern_count,
                "pattern_types": len(pattern_types)
            }
        )
    
    def _calculate_architecture_confidence(
        self,
        context_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> ConfidenceScore:
        """Calculate confidence in architecture analysis."""
        evidence = []
        factors = {}
        
        # Factor 1: Layer identification
        layers = context_results.get("architecture_layers", {})
        identified_layers = sum(1 for layer_data in layers.values() if layer_data.get("files", []))
        layer_score = min(1.0, identified_layers / 4.0)  # Normalize to 4 layers
        factors["layer_identification"] = layer_score
        evidence.append(f"Identified {identified_layers} architecture layers")
        
        # Factor 2: Component mapping
        components = context_results.get("components", [])
        component_score = min(1.0, len(components) / 10.0)  # Normalize to 10 components
        factors["component_mapping"] = component_score
        evidence.append(f"Mapped {len(components)} components")
        
        # Factor 3: Dependency analysis
        dependencies = context_results.get("dependencies_and_relationships", {})
        dep_analysis_score = 0.0
        if dependencies:
            if "imports" in dependencies:
                dep_analysis_score += 0.3
            if "circular_dependencies" in dependencies:
                dep_analysis_score += 0.3
            if "coupling_analysis" in dependencies:
                dep_analysis_score += 0.4
        
        factors["dependency_analysis"] = dep_analysis_score
        evidence.append(f"Dependency analysis completeness: {dep_analysis_score:.1%}")
        
        # Factor 4: Architecture coherence
        coherence_score = self._assess_architecture_coherence(context_results, analysis_results)
        factors["coherence"] = coherence_score
        evidence.append(f"Architecture coherence: {coherence_score:.2f}")
        
        # Calculate weighted score
        score = (
            layer_score * 0.3 +
            component_score * 0.2 +
            dep_analysis_score * 0.3 +
            coherence_score * 0.2
        )
        
        reasoning = f"Architecture confidence based on {identified_layers} layers and {len(components)} components"
        
        return ConfidenceScore(
            category=ConfidenceCategory.ARCHITECTURE,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "layers_identified": identified_layers,
                "components_mapped": len(components)
            }
        )
    
    def _calculate_security_confidence(
        self,
        analysis_results: Dict[str, Any]
    ) -> ConfidenceScore:
        """Calculate confidence in security analysis."""
        evidence = []
        factors = {}
        
        # Factor 1: Security scan coverage
        security_results = analysis_results.get("security", {})
        scan_coverage = 0.0
        
        if "vulnerabilities" in security_results:
            scan_coverage += 0.4
        if "security_patterns" in security_results:
            scan_coverage += 0.3
        if "risk_assessment" in security_results:
            scan_coverage += 0.3
        
        factors["scan_coverage"] = scan_coverage
        evidence.append(f"Security scan coverage: {scan_coverage:.1%}")
        
        # Factor 2: Vulnerability detection confidence
        vulnerabilities = security_results.get("vulnerabilities", [])
        if vulnerabilities:
            vuln_confidences = [v.get("confidence", 0.5) for v in vulnerabilities if isinstance(v, dict)]
            avg_vuln_confidence = statistics.mean(vuln_confidences) if vuln_confidences else 0.5
            factors["vulnerability_confidence"] = avg_vuln_confidence
            evidence.append(f"Average vulnerability confidence: {avg_vuln_confidence:.2f}")
        else:
            factors["vulnerability_confidence"] = 0.8  # High confidence when no vulnerabilities found
            evidence.append("No vulnerabilities detected")
        
        # Factor 3: Security pattern recognition
        security_patterns = security_results.get("security_patterns", [])
        pattern_score = min(1.0, len(security_patterns) / 3.0)  # Normalize to 3 patterns
        factors["pattern_recognition"] = pattern_score
        evidence.append(f"Security patterns recognized: {len(security_patterns)}")
        
        # Factor 4: Risk assessment completeness
        risk_assessment = security_results.get("risk_assessment", {})
        risk_completeness = 0.0
        if risk_assessment:
            if "overall_risk" in risk_assessment:
                risk_completeness += 0.5
            if "risk_factors" in risk_assessment:
                risk_completeness += 0.5
        
        factors["risk_completeness"] = risk_completeness
        evidence.append(f"Risk assessment completeness: {risk_completeness:.1%}")
        
        # Calculate weighted score
        score = (
            scan_coverage * 0.3 +
            factors["vulnerability_confidence"] * 0.3 +
            pattern_score * 0.2 +
            risk_completeness * 0.2
        )
        
        reasoning = f"Security confidence based on {scan_coverage:.1%} scan coverage and {len(vulnerabilities)} vulnerabilities"
        
        return ConfidenceScore(
            category=ConfidenceCategory.SECURITY,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "vulnerabilities_found": len(vulnerabilities),
                "security_patterns": len(security_patterns)
            }
        )
    
    def _calculate_dependency_confidence(
        self,
        context_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> ConfidenceScore:
        """Calculate confidence in dependency analysis."""
        evidence = []
        factors = {}
        
        # Factor 1: Dependency mapping completeness
        dependencies = context_results.get("dependencies_and_relationships", {})
        imports = dependencies.get("imports", {})
        mapping_completeness = min(1.0, len(imports) / 10.0) if imports else 0.0
        factors["mapping_completeness"] = mapping_completeness
        evidence.append(f"Dependency mapping: {len(imports)} files analyzed")
        
        # Factor 2: Circular dependency detection
        circular_deps = dependencies.get("circular_dependencies", [])
        circular_detection_score = 1.0 if "circular_dependencies" in dependencies else 0.0
        factors["circular_detection"] = circular_detection_score
        evidence.append(f"Circular dependencies: {len(circular_deps)} found")
        
        # Factor 3: Coupling analysis
        coupling_analysis = dependencies.get("coupling_analysis", {})
        coupling_score = 0.0
        if coupling_analysis:
            analyzed_files = len(coupling_analysis)
            coupling_score = min(1.0, analyzed_files / 10.0)
        
        factors["coupling_analysis"] = coupling_score
        evidence.append(f"Coupling analysis: {len(coupling_analysis)} files")
        
        # Factor 4: External dependency identification
        external_deps = analysis_results.get("external_dependencies", [])
        external_score = min(1.0, len(external_deps) / 5.0)
        factors["external_dependencies"] = external_score
        evidence.append(f"External dependencies: {len(external_deps)} identified")
        
        # Calculate weighted score
        score = (
            mapping_completeness * 0.3 +
            circular_detection_score * 0.2 +
            coupling_score * 0.3 +
            external_score * 0.2
        )
        
        reasoning = f"Dependency confidence based on {len(imports)} mapped dependencies and {len(circular_deps)} circular deps"
        
        return ConfidenceScore(
            category=ConfidenceCategory.DEPENDENCIES,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "mapped_dependencies": len(imports),
                "circular_dependencies": len(circular_deps),
                "coupling_analyzed": len(coupling_analysis)
            }
        )
    
    def _calculate_recommendation_confidence(
        self,
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any],
        category_scores: Dict[ConfidenceCategory, ConfidenceScore]
    ) -> ConfidenceScore:
        """Calculate confidence in recommendations."""
        evidence = []
        factors = {}
        
        # Factor 1: Recommendation coverage
        recommendations = []
        if "recommendations" in analysis_results:
            recommendations.extend(analysis_results["recommendations"])
        if "summary" in context_results and "recommendations" in context_results["summary"]:
            recommendations.extend(context_results["summary"]["recommendations"])
        
        coverage_score = min(1.0, len(recommendations) / 5.0)
        factors["coverage"] = coverage_score
        evidence.append(f"Generated {len(recommendations)} recommendations")
        
        # Factor 2: Recommendation quality (based on underlying analysis confidence)
        analysis_confidence = category_scores.get(ConfidenceCategory.ANALYSIS, ConfidenceScore(
            ConfidenceCategory.ANALYSIS, 0.5, "", [], {}, {}
        )).score
        
        pattern_confidence = category_scores.get(ConfidenceCategory.PATTERN_DETECTION, ConfidenceScore(
            ConfidenceCategory.PATTERN_DETECTION, 0.5, "", [], {}, {}
        )).score
        
        quality_score = (analysis_confidence + pattern_confidence) / 2.0
        factors["quality"] = quality_score
        evidence.append(f"Recommendation quality score: {quality_score:.2f}")
        
        # Factor 3: Actionability assessment
        actionable_count = 0
        for rec in recommendations:
            if isinstance(rec, str):
                # Simple heuristic: actionable recommendations contain specific terms
                if any(term in rec.lower() for term in ["refactor", "implement", "add", "remove", "update", "fix"]):
                    actionable_count += 1
            elif isinstance(rec, dict) and rec.get("actionable", False):
                actionable_count += 1
        
        actionability_score = actionable_count / len(recommendations) if recommendations else 0.0
        factors["actionability"] = actionability_score
        evidence.append(f"Actionable recommendations: {actionable_count}/{len(recommendations)}")
        
        # Factor 4: Priority assignment
        prioritized_count = 0
        for rec in recommendations:
            if isinstance(rec, dict) and "priority" in rec:
                prioritized_count += 1
        
        priority_score = prioritized_count / len(recommendations) if recommendations else 0.0
        factors["priority_assignment"] = priority_score
        evidence.append(f"Prioritized recommendations: {prioritized_count}/{len(recommendations)}")
        
        # Calculate weighted score
        score = (
            coverage_score * 0.3 +
            quality_score * 0.3 +
            actionability_score * 0.2 +
            priority_score * 0.2
        )
        
        reasoning = f"Recommendation confidence based on {len(recommendations)} recommendations with {quality_score:.2f} quality"
        
        return ConfidenceScore(
            category=ConfidenceCategory.RECOMMENDATIONS,
            score=score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "total_recommendations": len(recommendations),
                "actionable_recommendations": actionable_count,
                "prioritized_recommendations": prioritized_count
            }
        )
    
    def _calculate_overall_confidence(
        self,
        category_scores: Dict[ConfidenceCategory, ConfidenceScore]
    ) -> ConfidenceScore:
        """Calculate overall confidence score."""
        evidence = []
        factors = {}
        
        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0
        
        for category, weight in self.category_weights.items():
            if category in category_scores:
                score = category_scores[category].score
                weighted_sum += score * weight
                total_weight += weight
                factors[category.value] = score
                evidence.append(f"{category.value}: {score:.2f}")
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Apply confidence modifiers
        confidence_modifiers = self._calculate_confidence_modifiers(category_scores)
        modified_score = overall_score * confidence_modifiers["modifier"]
        
        factors.update(confidence_modifiers)
        evidence.extend(confidence_modifiers["evidence"])
        
        reasoning = f"Overall confidence: {overall_score:.2f} (modified: {modified_score:.2f})"
        
        return ConfidenceScore(
            category=ConfidenceCategory.OVERALL,
            score=modified_score,
            reasoning=reasoning,
            evidence=evidence,
            factors=factors,
            metadata={
                "base_score": overall_score,
                "modifier": confidence_modifiers["modifier"],
                "category_count": len(category_scores)
            }
        )
    
    def _calculate_confidence_modifiers(
        self,
        category_scores: Dict[ConfidenceCategory, ConfidenceScore]
    ) -> Dict[str, Any]:
        """Calculate confidence modifiers based on score distribution."""
        scores = [score.score for score in category_scores.values() if score.category != ConfidenceCategory.OVERALL]
        
        if not scores:
            return {"modifier": 1.0, "evidence": ["No category scores available"]}
        
        evidence = []
        modifier = 1.0
        
        # Consistency modifier
        score_std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        if score_std < 0.1:
            modifier *= 1.1  # Boost for consistent scores
            evidence.append("Consistent scores across categories (+10%)")
        elif score_std > 0.3:
            modifier *= 0.9  # Penalty for inconsistent scores
            evidence.append("Inconsistent scores across categories (-10%)")
        
        # Low score penalty
        low_scores = [s for s in scores if s < 0.3]
        if len(low_scores) > len(scores) * 0.5:
            modifier *= 0.8  # Penalty if more than half the scores are low
            evidence.append("Multiple low confidence categories (-20%)")
        
        # High score bonus
        high_scores = [s for s in scores if s > 0.8]
        if len(high_scores) > len(scores) * 0.7:
            modifier *= 1.1  # Bonus if most scores are high
            evidence.append("Multiple high confidence categories (+10%)")
        
        return {
            "modifier": modifier,
            "evidence": evidence,
            "score_std": score_std,
            "low_score_count": len(low_scores),
            "high_score_count": len(high_scores)
        }
    
    def _assess_content_quality(self, files: List[Dict[str, Any]]) -> float:
        """Assess the quality of file content for parsing confidence."""
        if not files:
            return 0.0
        
        quality_indicators = 0
        total_files = len(files)
        
        for file_info in files:
            content = file_info.get("content", "")
            if not content:
                continue
            
            # Check for code structure indicators
            if any(indicator in content for indicator in ["class ", "def ", "function ", "import ", "from "]):
                quality_indicators += 1
            
            # Check for reasonable content length
            if 50 < len(content) < 50000:  # Not too short or too long
                quality_indicators += 0.5
            
            # Check for proper encoding (no weird characters)
            try:
                content.encode('utf-8')
                quality_indicators += 0.3
            except UnicodeEncodeError:
                pass
        
        return min(1.0, quality_indicators / total_files)
    
    def _assess_result_consistency(self, analysis_results: Dict[str, Any]) -> float:
        """Assess consistency of analysis results."""
        consistency_score = 0.0
        
        # Check if complexity metrics are reasonable
        if "complexity" in analysis_results:
            complexity = analysis_results["complexity"]
            if isinstance(complexity, dict):
                cyclomatic = complexity.get("cyclomatic_complexity", 0)
                if 1 <= cyclomatic <= 50:  # Reasonable range
                    consistency_score += 0.3
        
        # Check if patterns and anti-patterns don't contradict
        patterns = analysis_results.get("patterns", [])
        anti_patterns = analysis_results.get("anti_patterns", [])
        
        if patterns or anti_patterns:
            # Simple check: if we have patterns, we should have some structure
            if patterns and "complexity" in analysis_results:
                consistency_score += 0.3
        
        # Check if security results are consistent with code patterns
        security = analysis_results.get("security", {})
        if security:
            vulnerabilities = security.get("vulnerabilities", [])
            # If we have security analysis, it should be consistent with patterns
            if isinstance(vulnerabilities, list):
                consistency_score += 0.4
        
        return min(1.0, consistency_score)
    
    def _assess_architecture_coherence(
        self,
        context_results: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> float:
        """Assess coherence of architecture analysis."""
        coherence_score = 0.0
        
        # Check layer consistency
        layers = context_results.get("architecture_layers", {})
        if layers:
            # Check if layers have reasonable file distribution
            layer_sizes = [len(layer_data.get("files", [])) for layer_data in layers.values()]
            if layer_sizes and max(layer_sizes) > 0:
                # Good if no single layer dominates completely
                max_ratio = max(layer_sizes) / sum(layer_sizes)
                if max_ratio < 0.8:  # No layer has more than 80% of files
                    coherence_score += 0.4
        
        # Check dependency coherence
        dependencies = context_results.get("dependencies_and_relationships", {})
        if dependencies:
            circular_deps = dependencies.get("circular_dependencies", [])
            coupling_analysis = dependencies.get("coupling_analysis", {})
            
            # Good architecture has few circular dependencies
            if len(circular_deps) == 0:
                coherence_score += 0.3
            elif len(circular_deps) < 3:
                coherence_score += 0.1
            
            # Good architecture has reasonable coupling
            if coupling_analysis:
                high_coupling = sum(1 for data in coupling_analysis.values() 
                                  if data.get("level") == "High")
                total_analyzed = len(coupling_analysis)
                if high_coupling / total_analyzed < 0.3:  # Less than 30% high coupling
                    coherence_score += 0.3
        
        return min(1.0, coherence_score)
    
    def get_confidence_summary(
        self,
        confidence_scores: Dict[ConfidenceCategory, ConfidenceScore]
    ) -> Dict[str, Any]:
        """Generate a summary of confidence scores."""
        summary = {
            "overall_confidence": confidence_scores.get(ConfidenceCategory.OVERALL, ConfidenceScore(
                ConfidenceCategory.OVERALL, 0.0, "", [], {}, {}
            )).score,
            "category_scores": {
                category.value: score.score 
                for category, score in confidence_scores.items()
            },
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        # Identify strengths (scores > 0.7)
        for category, score in confidence_scores.items():
            if score.score > 0.7:
                summary["strengths"].append({
                    "category": category.value,
                    "score": score.score,
                    "reasoning": score.reasoning
                })
        
        # Identify weaknesses (scores < 0.4)
        for category, score in confidence_scores.items():
            if score.score < 0.4:
                summary["weaknesses"].append({
                    "category": category.value,
                    "score": score.score,
                    "reasoning": score.reasoning
                })
        
        # Generate improvement recommendations
        if summary["weaknesses"]:
            summary["recommendations"].append("Focus on improving low-confidence areas")
        
        if len(summary["strengths"]) > len(summary["weaknesses"]):
            summary["recommendations"].append("Leverage high-confidence insights for decision making")
        
        return summary
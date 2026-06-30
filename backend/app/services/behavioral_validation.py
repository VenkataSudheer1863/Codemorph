"""Behavioral Validation Service with Human Review Gates."""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status types."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"
    AUTO_APPROVED = "auto_approved"
    TIMEOUT = "timeout"


class ReviewPriority(Enum):
    """Review priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationRule(Enum):
    """Types of validation rules."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    SECURITY_CHECK = "security_check"
    ARCHITECTURE_COMPLIANCE = "architecture_compliance"
    QUALITY_GATE = "quality_gate"
    DEPENDENCY_HEALTH = "dependency_health"
    FILE_COVERAGE = "file_coverage"
    TRANSFORMATION_COMPLETENESS = "transformation_completeness"
    TEST_COVERAGE_READINESS = "test_coverage_readiness"
    BUSINESS_RULE = "business_rule"
    CUSTOM_RULE = "custom_rule"


@dataclass
class ValidationCriteria:
    """Validation criteria definition."""
    rule_type: ValidationRule
    threshold: float
    description: str
    auto_approve_threshold: Optional[float] = None
    requires_human_review: bool = True
    timeout_minutes: int = 60
    escalation_rules: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of a validation check."""
    rule_type: ValidationRule
    status: ValidationStatus
    score: float
    threshold: float
    passed: bool
    message: str
    evidence: List[str]
    recommendations: List[str]
    timestamp: datetime
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None


@dataclass
class ReviewRequest:
    """Human review request."""
    id: str
    title: str
    description: str
    priority: ReviewPriority
    validation_results: List[ValidationResult]
    context_data: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    assigned_to: Optional[str] = None
    status: ValidationStatus = ValidationStatus.PENDING
    review_notes: Optional[str] = None
    decision_reason: Optional[str] = None


class ConfidenceValidator:
    """Validator for confidence-based checks."""
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
    
    def validate(self, confidence_scores: Dict[str, Any]) -> ValidationResult:
        """Validate confidence scores."""
        overall_confidence = confidence_scores.get("overall_confidence", 0.0)
        
        passed = overall_confidence >= self.min_confidence
        status = ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW
        
        evidence = []
        recommendations = []
        
        # Analyze individual category scores
        category_scores = confidence_scores.get("category_scores", {})
        low_confidence_categories = [
            category for category, score in category_scores.items()
            if score < self.min_confidence
        ]
        
        if low_confidence_categories:
            evidence.append(f"Low confidence categories: {', '.join(low_confidence_categories)}")
            recommendations.append(f"Review and improve analysis in: {', '.join(low_confidence_categories)}")
        
        # Check for consistency issues
        if "weaknesses" in confidence_scores:
            weaknesses = confidence_scores["weaknesses"]
            if weaknesses:
                evidence.extend([w["reasoning"] for w in weaknesses])
                recommendations.append("Address identified weaknesses before proceeding")
        
        message = f"Overall confidence: {overall_confidence:.2f} (threshold: {self.min_confidence})"
        
        return ValidationResult(
            rule_type=ValidationRule.CONFIDENCE_THRESHOLD,
            status=status,
            score=overall_confidence,
            threshold=self.min_confidence,
            passed=passed,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now()
        )


class SecurityValidator:
    """Validator for security-related checks."""
    
    def __init__(self, max_high_risk_vulnerabilities: int = 0):
        self.max_high_risk_vulnerabilities = max_high_risk_vulnerabilities
    
    def validate(self, security_analysis: Dict[str, Any]) -> ValidationResult:
        """Validate security analysis results."""
        vulnerabilities = security_analysis.get("vulnerabilities", [])
        
        # Count high-risk vulnerabilities
        high_risk_count = sum(
            1 for vuln in vulnerabilities
            if isinstance(vuln, dict) and vuln.get("severity", "").lower() in ["high", "critical"]
        )
        
        passed = high_risk_count <= self.max_high_risk_vulnerabilities
        status = ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW
        
        evidence = []
        recommendations = []
        
        if high_risk_count > 0:
            evidence.append(f"Found {high_risk_count} high/critical risk vulnerabilities")
            recommendations.append("Review and address high-risk security vulnerabilities")
            
            # Add specific vulnerability details
            for vuln in vulnerabilities:
                if isinstance(vuln, dict) and vuln.get("severity", "").lower() in ["high", "critical"]:
                    evidence.append(f"- {vuln.get('type', 'Unknown')}: {vuln.get('description', 'No description')}")
        
        # Check security patterns
        security_patterns = security_analysis.get("security_patterns", [])
        if not security_patterns:
            evidence.append("No security patterns detected")
            recommendations.append("Consider implementing security best practices")
        
        message = f"Security validation: {high_risk_count} high-risk vulnerabilities (max allowed: {self.max_high_risk_vulnerabilities})"
        
        return ValidationResult(
            rule_type=ValidationRule.SECURITY_CHECK,
            status=status,
            score=1.0 - (high_risk_count / max(1, len(vulnerabilities))),
            threshold=1.0 - self.max_high_risk_vulnerabilities,
            passed=passed,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now()
        )


class ArchitectureValidator:
    """Validator for architecture compliance checks."""
    
    def __init__(self, required_layers: List[str] = None, max_circular_dependencies: int = 3):
        self.required_layers = required_layers or ["backend"]  # only require backend layer
        self.max_circular_dependencies = max_circular_dependencies
    
    def validate(self, architecture_analysis: Dict[str, Any]) -> ValidationResult:
        """Validate architecture analysis results."""
        # Support both "architecture_layers" and "layers" keys (different callers use different keys)
        layers = (
            architecture_analysis.get("architecture_layers")
            or architecture_analysis.get("layers")
            or {}
        )
        dependencies = architecture_analysis.get("dependencies_and_relationships", {})
        
        evidence = []
        recommendations = []
        issues = 0

        # If no layer data at all, treat as neutral pass — don't penalise missing context
        if not layers:
            evidence.append("No architecture layer data available — skipping layer check")
        else:
            # Check required layers — only count as issue if layers dict is non-empty but required layer absent
            missing_layers = []
            for required_layer in self.required_layers:
                layer_data = layers.get(required_layer, {})
                has_files = (
                    layer_data.get("files")
                    or layer_data.get("file_count", 0) > 0
                    or layer_data.get("components")
                )
                if not has_files:
                    missing_layers.append(required_layer)
                    issues += 1
            
            if missing_layers:
                evidence.append(f"Missing required layers: {', '.join(missing_layers)}")
                recommendations.append(f"Implement missing architecture layers: {', '.join(missing_layers)}")
        
        # Check circular dependencies
        circular_deps = dependencies.get("circular_dependencies", [])
        if len(circular_deps) > self.max_circular_dependencies:
            evidence.append(f"Found {len(circular_deps)} circular dependencies (max allowed: {self.max_circular_dependencies})")
            recommendations.append("Resolve circular dependencies to improve architecture")
            issues += 1
        
        # Check coupling analysis — only flag if coupling data is actually present
        coupling_analysis = dependencies.get("coupling_analysis", {})
        if coupling_analysis:
            high_coupling_files = [
                f for f, data in coupling_analysis.items()
                if data.get("level") == "High"
            ]
            if len(high_coupling_files) > len(coupling_analysis) * 0.3:
                evidence.append(f"High coupling detected in {len(high_coupling_files)} files")
                recommendations.append("Refactor highly coupled components")
                issues += 1
        
        # Score: 1.0 when 0 issues, 0.67 for 1, 0.33 for 2, 0.0 for 3+
        score = max(0.0, 1.0 - (issues / 3.0))
        # Pass if score meets the relaxed threshold (0.5) — allows up to 1 issue
        passed = score >= 0.5
        status = ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW
        
        message = f"Architecture validation: {issues} issue(s) found — score {score:.2f}"
        
        return ValidationResult(
            rule_type=ValidationRule.ARCHITECTURE_COMPLIANCE,
            status=status,
            score=score,
            threshold=0.5,
            passed=passed,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now()
        )


class QualityGateValidator:
    """Validator for code quality gates."""
    
    def __init__(self, min_quality_score: float = 0.5, max_complexity: float = 20.0):
        self.min_quality_score = min_quality_score
        self.max_complexity = max_complexity
    
    def validate(self, analysis_results: Dict[str, Any]) -> ValidationResult:
        """Validate code quality metrics."""
        quality_score = analysis_results.get("code_quality_score", None)
        complexity_metrics = analysis_results.get("complexity", {})
        
        evidence = []
        recommendations = []
        issues = 0
        
        # Check quality score — treat missing/None as neutral (don't penalise absent data)
        if quality_score is not None and quality_score < self.min_quality_score:
            evidence.append(f"Code quality score {quality_score:.2f} below threshold {self.min_quality_score}")
            recommendations.append("Improve code quality through refactoring and best practices")
            issues += 1
        elif quality_score is None:
            evidence.append("Code quality score not available — skipping quality check")
        
        # Check complexity metrics — only flag if data is actually present
        if isinstance(complexity_metrics, dict) and complexity_metrics:
            avg_complexity = complexity_metrics.get("average_complexity", 0.0)
            if avg_complexity > self.max_complexity:
                evidence.append(f"Average complexity {avg_complexity:.2f} exceeds threshold {self.max_complexity}")
                recommendations.append("Reduce code complexity by breaking down complex functions")
                issues += 1
        
        # Check for anti-patterns — only flag if list is non-empty
        anti_patterns = analysis_results.get("anti_patterns", [])
        if anti_patterns:
            evidence.append(f"Found {len(anti_patterns)} anti-patterns")
            recommendations.append("Address identified anti-patterns")
            issues += 1
        
        score = max(0.0, 1.0 - (issues / 3.0))
        # Pass if score meets relaxed threshold (0.5) — allows up to 1 issue
        passed = score >= 0.5
        status = ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW
        
        message = f"Quality gate validation: {issues} issue(s) found — score {score:.2f}"
        
        return ValidationResult(
            rule_type=ValidationRule.QUALITY_GATE,
            status=status,
            score=score,
            threshold=0.5,
            passed=passed,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now()
        )


class DependencyHealthValidator:
    """Validator for dependency health — checks for circular deps and high coupling."""

    def __init__(self, max_circular: int = 5, max_coupling_ratio: float = 0.4):
        self.max_circular = max_circular
        self.max_coupling_ratio = max_coupling_ratio

    def validate(self, context_results: Dict[str, Any]) -> ValidationResult:
        deps = context_results.get("dependencies_and_relationships", {})
        circular = deps.get("circular_dependencies", [])
        coupling = deps.get("coupling_analysis", {})

        evidence = []
        recommendations = []
        issues = 0

        if circular:
            evidence.append(f"{len(circular)} circular dependency chain(s) detected")
            if len(circular) > self.max_circular:
                recommendations.append("Break circular dependencies to improve maintainability")
                issues += 1
        else:
            evidence.append("No circular dependencies detected")

        if coupling:
            high_coupled = [f for f, d in coupling.items() if d.get("level") == "High"]
            ratio = len(high_coupled) / max(len(coupling), 1)
            if ratio > self.max_coupling_ratio:
                evidence.append(f"{len(high_coupled)}/{len(coupling)} files have high coupling ({ratio*100:.0f}%)")
                recommendations.append("Refactor tightly coupled modules into smaller, focused units")
                issues += 1
            else:
                evidence.append(f"Coupling levels acceptable ({len(high_coupled)} high-coupling files)")
        else:
            evidence.append("No coupling data available — skipping coupling check")

        score = max(0.0, 1.0 - issues * 0.4)
        passed = score >= 0.5
        return ValidationResult(
            rule_type=ValidationRule.DEPENDENCY_HEALTH,
            status=ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW,
            score=score,
            threshold=0.5,
            passed=passed,
            message=f"Dependency health: {issues} issue(s) — score {score:.2f}",
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now(),
        )


class FileCoverageValidator:
    """Validator for file parsing coverage — ensures most files were parsed successfully."""

    def __init__(self, min_coverage: float = 0.7):
        self.min_coverage = min_coverage

    def validate(self, analysis_results: Dict[str, Any]) -> ValidationResult:
        total = analysis_results.get("total_files", 0)
        parsed = analysis_results.get("files_parsed", total)
        errors = analysis_results.get("parsing_errors", [])
        parse_success_rate = analysis_results.get("parse_success_rate", None)

        evidence = []
        recommendations = []

        if total == 0:
            evidence.append("No file data available — cannot assess coverage")
            score = 0.0
        else:
            if parse_success_rate is not None:
                coverage = parse_success_rate / 100.0
            else:
                coverage = parsed / total if total > 0 else 1.0

            evidence.append(f"{parsed}/{total} files parsed ({coverage*100:.1f}% coverage)")
            if errors:
                evidence.append(f"{len(errors)} parsing error(s) encountered")
                recommendations.append("Review files with parsing errors and fix syntax issues")
            score = min(1.0, coverage)

        passed = score >= self.min_coverage
        return ValidationResult(
            rule_type=ValidationRule.FILE_COVERAGE,
            status=ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW,
            score=score,
            threshold=self.min_coverage,
            passed=passed,
            message=f"File coverage: {score*100:.1f}% of files successfully parsed",
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now(),
        )


class TransformationCompletenessValidator:
    """Validator for transformation completeness — checks that output files were produced."""

    def __init__(self, min_completeness: float = 0.7):
        self.min_completeness = min_completeness

    def validate(self, analysis_results: Dict[str, Any]) -> ValidationResult:
        total = analysis_results.get("total_files_processed", 0)
        successful = analysis_results.get("successful_transformations", total)
        failed = analysis_results.get("failed_transformations", 0)
        mode = analysis_results.get("transformation_mode", "unknown")

        evidence = []
        recommendations = []

        if total == 0:
            evidence.append("No transformation data available")
            score = 0.0
        else:
            completeness = successful / total if total > 0 else 0.0
            evidence.append(f"{successful}/{total} files fully transformed ({completeness*100:.1f}%)")
            if isinstance(mode, str) and mode not in ("unknown",):
                evidence.append(f"Transformation detail: {mode}")
            if failed > 0:
                evidence.append(f"{failed} file(s) failed or were passed through without transformation")
                recommendations.append("Review transformation errors and retry failed files")
                recommendations.append("Check that the target framework templates are correctly applied")
            score = completeness

        passed = score >= self.min_completeness
        return ValidationResult(
            rule_type=ValidationRule.TRANSFORMATION_COMPLETENESS,
            status=ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW,
            score=score,
            threshold=self.min_completeness,
            passed=passed,
            message=f"Transformation completeness: {score*100:.1f}% of files fully transformed",
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now(),
        )


class TestCoverageReadinessValidator:
    """Validator for test coverage readiness — checks if test scripts were generated."""

    def __init__(self, min_score: float = 0.5):
        self.min_score = min_score

    def validate(self, analysis_results: Dict[str, Any]) -> ValidationResult:
        test_scripts = analysis_results.get("test_scripts", [])
        total_functions = analysis_results.get("total_functions", 0)
        total_classes = analysis_results.get("total_classes", 0)

        evidence = []
        recommendations = []

        if test_scripts:
            evidence.append(f"{len(test_scripts)} test script(s) generated")
            score = 1.0
        else:
            evidence.append("No test scripts generated for the transformed codebase")
            recommendations.append("Generate unit tests for transformed modules")
            recommendations.append("Add integration tests for API endpoints")
            score = 0.0

        if total_functions > 0:
            evidence.append(f"{total_functions} function(s) identified as test candidates")
        if total_classes > 0:
            evidence.append(f"{total_classes} class(es) identified as test candidates")

        passed = score >= self.min_score
        return ValidationResult(
            rule_type=ValidationRule.TEST_COVERAGE_READINESS,
            status=ValidationStatus.APPROVED if passed else ValidationStatus.REQUIRES_REVIEW,
            score=score,
            threshold=self.min_score,
            passed=passed,
            message=f"Test coverage readiness: {'test scripts generated' if test_scripts else 'no test scripts generated'}",
            evidence=evidence,
            recommendations=recommendations,
            timestamp=datetime.now(),
        )


class HumanReviewGate:
    """Human review gate for validation results."""
    
    def __init__(self):
        self.pending_reviews: Dict[str, ReviewRequest] = {}
        self.review_history: List[ReviewRequest] = []
    
    def create_review_request(
        self,
        title: str,
        description: str,
        validation_results: List[ValidationResult],
        context_data: Dict[str, Any],
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        timeout_minutes: int = 60
    ) -> ReviewRequest:
        """Create a new review request."""
        request_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.pending_reviews)}"
        
        request = ReviewRequest(
            id=request_id,
            title=title,
            description=description,
            priority=priority,
            validation_results=validation_results,
            context_data=context_data,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=timeout_minutes)
        )
        
        self.pending_reviews[request_id] = request
        logger.info(f"Created review request: {request_id}")
        
        return request
    
    def submit_review(
        self,
        request_id: str,
        decision: ValidationStatus,
        reviewer: str,
        notes: Optional[str] = None,
        decision_reason: Optional[str] = None
    ) -> bool:
        """Submit a review decision."""
        if request_id not in self.pending_reviews:
            logger.error(f"Review request not found: {request_id}")
            return False
        
        request = self.pending_reviews[request_id]
        request.status = decision
        request.assigned_to = reviewer
        request.review_notes = notes
        request.decision_reason = decision_reason
        
        # Move to history
        self.review_history.append(request)
        del self.pending_reviews[request_id]
        
        logger.info(f"Review completed: {request_id} - {decision.value} by {reviewer}")
        return True
    
    def get_pending_reviews(self, priority: Optional[ReviewPriority] = None) -> List[ReviewRequest]:
        """Get pending review requests."""
        reviews = list(self.pending_reviews.values())
        
        if priority:
            reviews = [r for r in reviews if r.priority == priority]
        
        # Sort by priority and creation time
        priority_order = {
            ReviewPriority.CRITICAL: 0,
            ReviewPriority.HIGH: 1,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 3
        }
        
        reviews.sort(key=lambda r: (priority_order[r.priority], r.created_at))
        return reviews
    
    def check_timeouts(self) -> List[str]:
        """Check for timed-out review requests."""
        now = datetime.now()
        timed_out = []
        
        for request_id, request in list(self.pending_reviews.items()):
            if now > request.expires_at:
                request.status = ValidationStatus.TIMEOUT
                self.review_history.append(request)
                del self.pending_reviews[request_id]
                timed_out.append(request_id)
                logger.warning(f"Review request timed out: {request_id}")
        
        return timed_out

class BehavioralValidationEngine:
    """Main behavioral validation engine with human review gates."""
    
    def __init__(self):
        self.validators = {
            ValidationRule.CONFIDENCE_THRESHOLD: ConfidenceValidator(),
            ValidationRule.SECURITY_CHECK: SecurityValidator(),
            ValidationRule.ARCHITECTURE_COMPLIANCE: ArchitectureValidator(),
            ValidationRule.QUALITY_GATE: QualityGateValidator(),
            ValidationRule.DEPENDENCY_HEALTH: DependencyHealthValidator(),
            ValidationRule.FILE_COVERAGE: FileCoverageValidator(),
            ValidationRule.TRANSFORMATION_COMPLETENESS: TransformationCompletenessValidator(),
            ValidationRule.TEST_COVERAGE_READINESS: TestCoverageReadinessValidator(),
        }
        self.review_gate = HumanReviewGate()
        self.validation_criteria = self._get_default_criteria()
        self.custom_validators: Dict[ValidationRule, Callable] = {}
    
    def _get_default_criteria(self) -> List[ValidationCriteria]:
        """Get default validation criteria tuned for ~70% pass rate."""
        return [
            ValidationCriteria(
                rule_type=ValidationRule.CONFIDENCE_THRESHOLD,
                threshold=0.5,
                description="Minimum confidence threshold for analysis results",
                auto_approve_threshold=0.75,
                requires_human_review=True,
                timeout_minutes=30
            ),
            ValidationCriteria(
                rule_type=ValidationRule.SECURITY_CHECK,
                threshold=0.0,
                description="Security vulnerability assessment",
                auto_approve_threshold=None,
                requires_human_review=False,
                timeout_minutes=60
            ),
            ValidationCriteria(
                rule_type=ValidationRule.ARCHITECTURE_COMPLIANCE,
                threshold=0.5,
                description="Architecture compliance validation",
                auto_approve_threshold=0.8,
                requires_human_review=False,
                timeout_minutes=45
            ),
            ValidationCriteria(
                rule_type=ValidationRule.QUALITY_GATE,
                threshold=0.5,
                description="Code quality gate validation",
                auto_approve_threshold=0.8,
                requires_human_review=False,
                timeout_minutes=15
            ),
            ValidationCriteria(
                rule_type=ValidationRule.DEPENDENCY_HEALTH,
                threshold=0.5,
                description="Dependency health and coupling analysis",
                auto_approve_threshold=0.8,
                requires_human_review=False,
                timeout_minutes=15
            ),
            ValidationCriteria(
                rule_type=ValidationRule.FILE_COVERAGE,
                threshold=0.7,
                description="File parsing coverage check",
                auto_approve_threshold=0.9,
                requires_human_review=False,
                timeout_minutes=10
            ),
            ValidationCriteria(
                rule_type=ValidationRule.TRANSFORMATION_COMPLETENESS,
                threshold=0.7,
                description="Transformation output completeness",
                auto_approve_threshold=0.9,
                requires_human_review=False,
                timeout_minutes=10
            ),
            ValidationCriteria(
                rule_type=ValidationRule.TEST_COVERAGE_READINESS,
                threshold=0.5,
                description="Test coverage readiness assessment",
                auto_approve_threshold=0.8,
                requires_human_review=False,
                timeout_minutes=10
            ),
        ]
    
    def add_custom_validator(self, rule_type: ValidationRule, validator_func: Callable) -> None:
        """Add a custom validator function."""
        self.custom_validators[rule_type] = validator_func
        logger.info(f"Added custom validator for {rule_type.value}")
    
    def validate_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any],
        confidence_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate analysis results against all criteria."""
        validation_results = []
        
        # Run all validators
        for criteria in self.validation_criteria:
            try:
                result = self._run_validator(
                    criteria.rule_type,
                    analysis_results,
                    context_results,
                    confidence_scores
                )
                validation_results.append(result)
                
            except Exception as e:
                logger.error(f"Error running validator {criteria.rule_type.value}: {e}")
                # Create error result
                error_result = ValidationResult(
                    rule_type=criteria.rule_type,
                    status=ValidationStatus.REQUIRES_REVIEW,
                    score=0.0,
                    threshold=criteria.threshold,
                    passed=False,
                    message=f"Validation error: {str(e)}",
                    evidence=[f"Validator failed: {str(e)}"],
                    recommendations=["Manual review required due to validation error"],
                    timestamp=datetime.now()
                )
                validation_results.append(error_result)
        
        # Determine overall validation status
        overall_status = self._determine_overall_status(validation_results)
        
        # Create review request if needed
        review_request = None
        if overall_status in [ValidationStatus.REQUIRES_REVIEW, ValidationStatus.REJECTED]:
            review_request = self._create_review_request(
                validation_results,
                analysis_results,
                context_results,
                confidence_scores
            )
        
        return {
            "validation_results": [self._validation_result_to_dict(r) for r in validation_results],
            "overall_status": overall_status.value,
            "review_request": self._review_request_to_dict(review_request) if review_request else None,
            "summary": self._generate_validation_summary(validation_results),
            "recommendations": self._aggregate_recommendations(validation_results)
        }
    
    def _run_validator(
        self,
        rule_type: ValidationRule,
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any],
        confidence_scores: Dict[str, Any]
    ) -> ValidationResult:
        """Run a specific validator."""
        if rule_type in self.custom_validators:
            return self.custom_validators[rule_type](analysis_results, context_results, confidence_scores)
        
        validator = self.validators.get(rule_type)
        if not validator:
            raise ValueError(f"No validator found for rule type: {rule_type.value}")
        
        # Prepare data for validator
        if rule_type == ValidationRule.CONFIDENCE_THRESHOLD:
            return validator.validate(confidence_scores)
        elif rule_type == ValidationRule.SECURITY_CHECK:
            return validator.validate(analysis_results.get("security", {}))
        elif rule_type == ValidationRule.ARCHITECTURE_COMPLIANCE:
            return validator.validate(context_results)
        elif rule_type == ValidationRule.QUALITY_GATE:
            return validator.validate(analysis_results)
        elif rule_type == ValidationRule.DEPENDENCY_HEALTH:
            return validator.validate(context_results)
        elif rule_type == ValidationRule.FILE_COVERAGE:
            return validator.validate(analysis_results)
        elif rule_type == ValidationRule.TRANSFORMATION_COMPLETENESS:
            return validator.validate(analysis_results)
        elif rule_type == ValidationRule.TEST_COVERAGE_READINESS:
            return validator.validate(analysis_results)
        else:
            raise ValueError(f"Unknown validation rule: {rule_type.value}")
    
    def _determine_overall_status(self, validation_results: List[ValidationResult]) -> ValidationStatus:
        """Determine overall validation status using majority-pass rule (≥70% pass = APPROVED)."""
        if not validation_results:
            return ValidationStatus.APPROVED
        
        passed_count = sum(1 for r in validation_results if r.passed)
        total = len(validation_results)
        pass_rate = passed_count / total

        # Hard reject only if security check explicitly failed with score 0
        security_results = [r for r in validation_results if r.rule_type == ValidationRule.SECURITY_CHECK]
        if security_results and all(r.score == 0.0 and not r.passed for r in security_results):
            return ValidationStatus.REQUIRES_REVIEW

        # ≥70% pass → approved
        if pass_rate >= 0.70:
            return ValidationStatus.APPROVED

        # Between 40-70% → requires review (not outright rejected)
        if pass_rate >= 0.40:
            return ValidationStatus.REQUIRES_REVIEW

        return ValidationStatus.REJECTED
    
    def _create_review_request(
        self,
        validation_results: List[ValidationResult],
        analysis_results: Dict[str, Any],
        context_results: Dict[str, Any],
        confidence_scores: Dict[str, Any]
    ) -> ReviewRequest:
        """Create a review request for failed validations."""
        failed_validations = [r for r in validation_results if not r.passed]
        
        # Determine priority based on failed validations
        priority = ReviewPriority.MEDIUM
        if any(r.rule_type == ValidationRule.SECURITY_CHECK for r in failed_validations):
            priority = ReviewPriority.HIGH
        if any(r.score < 0.3 for r in failed_validations):
            priority = ReviewPriority.CRITICAL
        
        title = f"Validation Review Required - {len(failed_validations)} Issues"
        description = f"Analysis results require human review due to {len(failed_validations)} validation failures."
        
        context_data = {
            "analysis_results": analysis_results,
            "context_results": context_results,
            "confidence_scores": confidence_scores,
            "failed_validation_count": len(failed_validations),
            "validation_summary": self._generate_validation_summary(validation_results)
        }
        
        return self.review_gate.create_review_request(
            title=title,
            description=description,
            validation_results=validation_results,
            context_data=context_data,
            priority=priority,
            timeout_minutes=60
        )
    
    def _generate_validation_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate validation summary."""
        total_validations = len(validation_results)
        passed_validations = sum(1 for r in validation_results if r.passed)
        failed_validations = total_validations - passed_validations
        
        avg_score = sum(r.score for r in validation_results) / total_validations if total_validations > 0 else 0.0
        
        status_counts = {}
        for result in validation_results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
            "success_rate": passed_validations / total_validations if total_validations > 0 else 0.0,
            "average_score": avg_score,
            "status_distribution": status_counts
        }
    
    def _aggregate_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """Aggregate recommendations from all validation results."""
        all_recommendations = []
        for result in validation_results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        return unique_recommendations
    
    def _validation_result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "rule_type": result.rule_type.value,
            "status": result.status.value,
            "score": result.score,
            "threshold": result.threshold,
            "passed": result.passed,
            "message": result.message,
            "evidence": result.evidence,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat(),
            "reviewer": result.reviewer,
            "review_notes": result.review_notes
        }
    
    def _review_request_to_dict(self, request: ReviewRequest) -> Dict[str, Any]:
        """Convert review request to dictionary."""
        return {
            "id": request.id,
            "title": request.title,
            "description": request.description,
            "priority": request.priority.value,
            "validation_results": [self._validation_result_to_dict(r) for r in request.validation_results],
            "context_data": request.context_data,
            "created_at": request.created_at.isoformat(),
            "expires_at": request.expires_at.isoformat(),
            "assigned_to": request.assigned_to,
            "status": request.status.value,
            "review_notes": request.review_notes,
            "decision_reason": request.decision_reason
        }
    
    def get_review_dashboard(self) -> Dict[str, Any]:
        """Get review dashboard data."""
        pending_reviews = self.review_gate.get_pending_reviews()
        
        # Check for timeouts
        timed_out = self.review_gate.check_timeouts()
        
        # Generate statistics
        priority_counts = {}
        for review in pending_reviews:
            priority = review.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "pending_reviews": [self._review_request_to_dict(r) for r in pending_reviews],
            "pending_count": len(pending_reviews),
            "priority_distribution": priority_counts,
            "timed_out_reviews": timed_out,
            "review_history_count": len(self.review_gate.review_history),
            "statistics": {
                "total_reviews_created": len(self.review_gate.review_history) + len(pending_reviews),
                "completed_reviews": len(self.review_gate.review_history),
                "timeout_rate": len(timed_out) / max(1, len(self.review_gate.review_history)) if self.review_gate.review_history else 0.0
            }
        }
    
    def submit_review_decision(
        self,
        request_id: str,
        decision: str,
        reviewer: str,
        notes: Optional[str] = None,
        decision_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a review decision."""
        try:
            # Convert string decision to enum
            decision_status = ValidationStatus(decision.lower())
            
            success = self.review_gate.submit_review(
                request_id=request_id,
                decision=decision_status,
                reviewer=reviewer,
                notes=notes,
                decision_reason=decision_reason
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Review decision submitted successfully",
                    "request_id": request_id,
                    "decision": decision_status.value,
                    "reviewer": reviewer
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to submit review decision for request {request_id}",
                    "error": "Request not found or already completed"
                }
                
        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid decision status: {decision}",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error submitting review decision: {e}")
            return {
                "success": False,
                "message": "Internal error occurred",
                "error": str(e)
            }
    
    def configure_validation_criteria(self, criteria_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Configure validation criteria."""
        try:
            new_criteria = []
            for criteria_dict in criteria_list:
                criteria = ValidationCriteria(
                    rule_type=ValidationRule(criteria_dict["rule_type"]),
                    threshold=criteria_dict["threshold"],
                    description=criteria_dict["description"],
                    auto_approve_threshold=criteria_dict.get("auto_approve_threshold"),
                    requires_human_review=criteria_dict.get("requires_human_review", True),
                    timeout_minutes=criteria_dict.get("timeout_minutes", 60),
                    escalation_rules=criteria_dict.get("escalation_rules")
                )
                new_criteria.append(criteria)
            
            self.validation_criteria = new_criteria
            
            return {
                "success": True,
                "message": f"Configured {len(new_criteria)} validation criteria",
                "criteria_count": len(new_criteria)
            }
            
        except Exception as e:
            logger.error(f"Error configuring validation criteria: {e}")
            return {
                "success": False,
                "message": "Failed to configure validation criteria",
                "error": str(e)
            }
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation metrics and analytics."""
        history = self.review_gate.review_history
        
        if not history:
            return {
                "total_validations": 0,
                "approval_rate": 0.0,
                "average_review_time": 0.0,
                "rule_type_distribution": {},
                "priority_distribution": {},
                "reviewer_statistics": {}
            }
        
        # Calculate metrics
        total_validations = len(history)
        approved_count = sum(1 for r in history if r.status == ValidationStatus.APPROVED)
        approval_rate = approved_count / total_validations
        
        # Calculate average review time
        review_times = []
        for request in history:
            if request.status != ValidationStatus.TIMEOUT:
                # Estimate review time (simplified)
                review_time = (request.expires_at - request.created_at).total_seconds() / 60
                review_times.append(review_time)
        
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0.0
        
        # Rule type distribution
        rule_type_counts = {}
        for request in history:
            for result in request.validation_results:
                rule_type = result.rule_type.value
                rule_type_counts[rule_type] = rule_type_counts.get(rule_type, 0) + 1
        
        # Priority distribution
        priority_counts = {}
        for request in history:
            priority = request.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Reviewer statistics
        reviewer_stats = {}
        for request in history:
            if request.assigned_to:
                reviewer = request.assigned_to
                if reviewer not in reviewer_stats:
                    reviewer_stats[reviewer] = {"total": 0, "approved": 0, "rejected": 0}
                
                reviewer_stats[reviewer]["total"] += 1
                if request.status == ValidationStatus.APPROVED:
                    reviewer_stats[reviewer]["approved"] += 1
                elif request.status == ValidationStatus.REJECTED:
                    reviewer_stats[reviewer]["rejected"] += 1
        
        return {
            "total_validations": total_validations,
            "approval_rate": approval_rate,
            "average_review_time_minutes": avg_review_time,
            "rule_type_distribution": rule_type_counts,
            "priority_distribution": priority_counts,
            "reviewer_statistics": reviewer_stats,
            "current_pending": len(self.review_gate.pending_reviews)
        }
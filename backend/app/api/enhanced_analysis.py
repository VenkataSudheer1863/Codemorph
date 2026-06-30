"""Enhanced Analysis API Endpoints."""

import re
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database.db import get_db
from ..models.project import Project
from ..services.database_analyzer import DatabaseAnalyzer
from ..services.api_converter import APIConverter
from ..services.behavioral_validation import BehavioralValidationEngine
from ..agents.orchestrator import CodeMorphOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enhanced", tags=["enhanced-analysis"])

# Pydantic models for request/response
class ValidationDecisionRequest(BaseModel):
    decision: str  # approved, rejected, requires_review
    reviewer: str
    notes: Optional[str] = None
    decision_reason: Optional[str] = None

class ValidationCriteriaRequest(BaseModel):
    criteria: List[Dict[str, Any]]

class DatabaseAnalysisResponse(BaseModel):
    schemas: List[Dict[str, Any]]
    orm_models: Dict[str, str]
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

class APIAnalysisResponse(BaseModel):
    endpoints: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    frameworks: List[str]
    openapi_spec: Dict[str, Any]
    statistics: Dict[str, Any]
    postman_collection: Dict[str, Any] = {}
    curl_examples: List[Dict[str, Any]] = []
    conversion_summary: Dict[str, Any] = {}


# Initialize services
database_analyzer = DatabaseAnalyzer()
api_converter = APIConverter()
validation_engine = BehavioralValidationEngine()


@router.post("/database-analysis/{project_id}")
async def analyze_database(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run enhanced database analysis for a project."""
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get project files (simplified - would need actual file retrieval)
        files = []  # This would be populated from actual project files
        
        # Run database analysis in background
        background_tasks.add_task(_run_database_analysis, project_id, files)
        
        return {
            "message": "Database analysis started",
            "project_id": project_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Database analysis failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-analysis/{project_id}/results")
async def get_database_analysis_results(
    project_id: str,
    db: Session = Depends(get_db)
) -> DatabaseAnalysisResponse:
    """Get database analysis results for a project."""
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get stored database analysis results
        # This would retrieve from database or cache
        results = _get_stored_database_results(project_id)
        
        return DatabaseAnalysisResponse(**results)
        
    except Exception as e:
        logger.error(f"Failed to get database analysis results for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-analysis/{project_id}")
async def analyze_api(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run API analysis on the converted codebase for a project."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        background_tasks.add_task(_run_api_analysis, project_id)

        return {
            "message": "API analysis started",
            "project_id": project_id,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"API analysis failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-analysis/{project_id}/results")
async def get_api_analysis_results(
    project_id: str,
    db: Session = Depends(get_db)
) -> APIAnalysisResponse:
    """Get API analysis results for the converted codebase."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        results = _get_stored_api_results(project_id)
        return APIAnalysisResponse(**results)

    except Exception as e:
        logger.error(f"Failed to get API analysis results for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation/results/{project_id}")
async def get_validation_results(project_id: str, db: Session = Depends(get_db)):
    """Get all validation results for a project with full detail."""
    try:
        from ..models.project import ValidationResult

        results = db.query(ValidationResult).filter(
            ValidationResult.project_id == project_id
        ).order_by(ValidationResult.created_at.desc()).all()

        return [
            {
                "id": r.id,
                "validation_type": r.validation_type,
                "status": r.status,
                "score": r.score,
                "threshold": r.threshold,
                "passed": r.passed,
                "message": r.message,
                "evidence": r.evidence or [],
                "recommendations": r.recommendations or [],
                "reviewer": r.reviewer,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Failed to get validation results for project {project_id}: {e}")
        return []


@router.get("/validation/dashboard")
async def get_validation_dashboard(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get behavioral validation dashboard. Optionally filter by project_id."""
    try:
        from ..models.project import ValidationResult, ReviewRequest
        
        # Get pending review requests — filter by project if provided
        review_query = db.query(ReviewRequest).filter(ReviewRequest.status == "pending")
        if project_id:
            review_query = review_query.filter(ReviewRequest.project_id == project_id)
        pending_reviews = review_query.all()
        
        # Get validation results for statistics
        val_query = db.query(ValidationResult)
        if project_id:
            val_query = val_query.filter(ValidationResult.project_id == project_id)
        validation_results = val_query.all()
        
        # Calculate priority distribution
        priority_distribution = {
            "critical": len([r for r in pending_reviews if r.priority == "critical"]),
            "high": len([r for r in pending_reviews if r.priority == "high"]),
            "medium": len([r for r in pending_reviews if r.priority == "medium"]),
            "low": len([r for r in pending_reviews if r.priority == "low"])
        }
        
        # Convert pending reviews to dict format
        pending_reviews_data = []
        for review in pending_reviews:
            # Get related validation results for this review
            related_validations = db.query(ValidationResult).filter(
                ValidationResult.project_id == review.project_id
            ).all()
            
            validation_results_data = []
            for val in related_validations:
                validation_results_data.append({
                    "rule_type": val.validation_type,
                    "status": val.status,
                    "score": val.score,
                    "threshold": val.threshold,
                    "passed": val.passed,
                    "message": val.message,
                    "evidence": val.evidence or [],
                    "recommendations": val.recommendations or [],
                    "timestamp": val.created_at.isoformat() if val.created_at else None,
                    "reviewer": val.reviewer
                })
            
            pending_reviews_data.append({
                "id": review.id,
                "title": review.title,
                "description": review.description,
                "priority": review.priority,
                "validation_results": validation_results_data,
                "context_data": review.context_data or {},
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "expires_at": review.expires_at.isoformat() if review.expires_at else None,
                "assigned_to": review.assigned_to,
                "status": review.status,
                "review_notes": review.review_notes,
                "decision_reason": review.decision_reason
            })
        
        # Calculate statistics
        total_reviews_query = db.query(ReviewRequest)
        completed_reviews_query = db.query(ReviewRequest).filter(
            ReviewRequest.status.in_(["approved", "rejected"])
        )
        if project_id:
            total_reviews_query = total_reviews_query.filter(ReviewRequest.project_id == project_id)
            completed_reviews_query = completed_reviews_query.filter(ReviewRequest.project_id == project_id)
        total_reviews = total_reviews_query.count()
        completed_reviews = completed_reviews_query.count()
        
        dashboard_data = {
            "pending_reviews": pending_reviews_data,
            "pending_count": len(pending_reviews),
            "priority_distribution": priority_distribution,
            "timed_out_reviews": [],  # Could implement timeout logic
            "review_history_count": completed_reviews,
            "statistics": {
                "total_reviews_created": total_reviews,
                "completed_reviews": completed_reviews,
                "timeout_rate": 0.0  # Could calculate based on expired reviews
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get validation dashboard: {e}")
        # Return empty structure instead of error for better UX
        return {
            "pending_reviews": [],
            "pending_count": 0,
            "priority_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "timed_out_reviews": [],
            "review_history_count": 0,
            "statistics": {
                "total_reviews_created": 0,
                "completed_reviews": 0,
                "timeout_rate": 0.0
            }
        }


@router.post("/validation/review/{request_id}")
async def submit_review_decision(
    request_id: str,
    decision_request: ValidationDecisionRequest
):
    """Submit a review decision for behavioral validation."""
    try:
        result = validation_engine.submit_review_decision(
            request_id=request_id,
            decision=decision_request.decision,
            reviewer=decision_request.reviewer,
            notes=decision_request.notes,
            decision_reason=decision_request.decision_reason
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "Review submission failed"))
        
    except Exception as e:
        logger.error(f"Failed to submit review decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation/metrics")
async def get_validation_metrics(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get validation metrics and analytics. Optionally filter by project_id."""
    try:
        from ..models.project import ValidationResult, ReviewRequest
        
        # Get validation results — filter by project if provided
        query = db.query(ValidationResult)
        if project_id:
            query = query.filter(ValidationResult.project_id == project_id)
        validation_results = query.all()

        review_query = db.query(ReviewRequest)
        if project_id:
            review_query = review_query.filter(ReviewRequest.project_id == project_id)
        review_requests = review_query.all()
        
        # Calculate metrics
        total_validations = len(validation_results)
        passed_validations = len([v for v in validation_results if v.passed])
        failed_validations = total_validations - passed_validations
        if total_validations == 0:
            approval_rate = 0.0
        else:
            approval_rate = round(passed_validations / total_validations * 100, 1)
        
        # Rule type distribution
        rule_type_distribution = {}
        for result in validation_results:
            rule_type = result.validation_type
            rule_type_distribution[rule_type] = rule_type_distribution.get(rule_type, 0) + 1
        
        # Priority distribution for reviews
        priority_distribution = {
            "critical": len([r for r in review_requests if r.priority == "critical"]),
            "high": len([r for r in review_requests if r.priority == "high"]),
            "medium": len([r for r in review_requests if r.priority == "medium"]),
            "low": len([r for r in review_requests if r.priority == "low"])
        }
        
        # Reviewer statistics
        reviewer_statistics = {}
        for result in validation_results:
            if result.reviewer:
                if result.reviewer not in reviewer_statistics:
                    reviewer_statistics[result.reviewer] = {"total": 0, "approved": 0, "rejected": 0}
                reviewer_statistics[result.reviewer]["total"] += 1
                if result.passed:
                    reviewer_statistics[result.reviewer]["approved"] += 1
                else:
                    reviewer_statistics[result.reviewer]["rejected"] += 1
        
        # Current pending reviews
        current_pending = len([r for r in review_requests if r.status == "pending"])
        
        metrics = {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
            "approval_rate": approval_rate,
            "average_review_time_minutes": 0.0,  # Could calculate from timestamps
            "rule_type_distribution": rule_type_distribution,
            "priority_distribution": priority_distribution,
            "reviewer_statistics": reviewer_statistics,
            "current_pending": current_pending
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get validation metrics: {e}")
        # Return empty structure instead of error for better UX
        return {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "approval_rate": 0.0,
            "average_review_time_minutes": 0.0,
            "rule_type_distribution": {},
            "priority_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "reviewer_statistics": {},
            "current_pending": 0
        }


@router.post("/validation/configure")
async def configure_validation_criteria(
    criteria_request: ValidationCriteriaRequest
):
    """Configure validation criteria."""
    try:
        result = validation_engine.configure_validation_criteria(criteria_request.criteria)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "Configuration failed"))
        
    except Exception as e:
        logger.error(f"Failed to configure validation criteria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependency-graphs/{project_id}")
async def get_dependency_graphs(project_id: str, db: Session = Depends(get_db)):
    """Return the initial and converted dependency graphs plus their comparison."""
    from ..models.project import Project, AnalysisResult

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    def _get(result_type: str):
        r = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == result_type,
        ).order_by(AnalysisResult.created_at.desc()).first()
        return r.data if r and r.data else {}

    def _ensure_metrics(graph: dict) -> dict:
        """Recount typed metrics from nodes/edges array if missing (handles old sparse graphs)."""
        if not graph:
            return graph
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        m = dict(graph.get("metrics", {}))
        if nodes and not m.get("file_nodes"):
            m["file_nodes"] = sum(1 for n in nodes if n.get("type") == "file")
            m["class_nodes"] = sum(1 for n in nodes if n.get("type") == "class")
            m["function_nodes"] = sum(1 for n in nodes if n.get("type") == "function")
        if edges and not m.get("import_edges"):
            m["import_edges"] = sum(1 for e in edges if e.get("type") == "import")
            m["contains_edges"] = sum(1 for e in edges if e.get("type") == "contains")
            m["inheritance_edges"] = sum(1 for e in edges if e.get("type") == "inheritance")
        m["total_nodes"] = len(nodes)
        m["total_edges"] = len(edges)
        graph = dict(graph)
        graph["metrics"] = m
        return graph

    initial = _ensure_metrics(_get("initial_dependency_graph"))
    converted = _ensure_metrics(_get("converted_dependency_graph"))
    comparison = _get("dependency_graph_comparison")

    # If no converted graph yet, try to derive initial from agentic_analysis
    if not initial:
        agentic = _get("agentic_analysis")
        initial = _ensure_metrics(agentic.get("dependency_graph", {}))

    # If comparison exists but used old metrics, recompute it
    if comparison and initial and converted:
        from ..api.pipeline import _compare_dependency_graphs
        comparison = _compare_dependency_graphs(initial, converted)

    return {
        "project_id": project_id,
        "initial_graph": initial,
        "converted_graph": converted,
        "comparison": comparison,
        "has_converted": bool(converted),
    }


@router.get("/audit/{project_id}")
async def get_audit_report(project_id: str, db: Session = Depends(get_db)):
    """Aggregate a post-conversion audit report from all stored analysis results."""
    from ..models.project import (
        Project, AnalysisResult, ParsedFile, ContextElement, ValidationResult
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ── Fetch stored analysis results ──────────────────────────────────────
    def get_result(result_type: str):
        r = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == result_type,
        ).order_by(AnalysisResult.created_at.desc()).first()
        return r.data if r and r.data else {}

    ingestion          = get_result("ingestion")
    parsing            = get_result("parsing")
    analysis           = get_result("analysis")
    agentic            = get_result("agentic_analysis")
    transformation_res = get_result("transformation_results")

    # ── ParsedFile rows ────────────────────────────────────────────────────
    parsed_files = db.query(ParsedFile).filter(ParsedFile.project_id == project_id).all()
    total_parsed = len(parsed_files)
    successful_parses = sum(1 for f in parsed_files if f.parsing_successful)
    failed_parses = total_parsed - successful_parses

    DECISION_KEYWORDS = re.compile(
        r'\b(if|elif|else|for|while|case|catch|except|and|or|&&|\|\|)\b', re.IGNORECASE
    )

    def _compute_complexity(f: ParsedFile) -> float:
        if f.complexity_score and f.complexity_score > 0:
            return f.complexity_score
        content = f.original_content or ""
        loc = max(f.lines_of_code or len(content.splitlines()), 1)
        decisions = len(DECISION_KEYWORDS.findall(content))
        return round(1 + (decisions / loc) * 100, 2)

    def _compute_maintainability(f: ParsedFile) -> float:
        if f.maintainability_index and f.maintainability_index > 0:
            return f.maintainability_index
        content = f.original_content or ""
        loc = max(f.lines_of_code or len(content.splitlines()), 1)
        decisions = len(DECISION_KEYWORDS.findall(content))
        avg_line_len = len(content) / loc
        mi = max(0.0, min(100.0, 100 - (decisions / loc * 50) - (avg_line_len / 10)))
        return round(mi, 2)

    all_complexity = [_compute_complexity(f) for f in parsed_files if f.original_content or (f.complexity_score and f.complexity_score > 0)]
    avg_complexity = round(sum(all_complexity) / len(all_complexity), 2) if all_complexity else None
    max_complexity = round(max(all_complexity), 2) if all_complexity else None

    all_maintainability = [_compute_maintainability(f) for f in parsed_files if f.original_content or (f.maintainability_index and f.maintainability_index > 0)]
    avg_maintainability = round(sum(all_maintainability) / len(all_maintainability), 2) if all_maintainability else None

    total_functions = parsing.get("total_functions") or sum(len(f.functions or []) for f in parsed_files)
    total_classes   = parsing.get("total_classes")   or sum(len(f.classes or []) for f in parsed_files)

    large_files          = [f.file_path for f in parsed_files if f.lines_of_code and f.lines_of_code > 500]
    god_class_candidates = [f.file_path for f in parsed_files if len(f.classes or []) > 5]
    backup_files         = [f.file_path for f in parsed_files if f.file_path.endswith((".bak", ".old", ".backup", ".orig"))]
    linting_violations   = sum(len(f.parsing_errors or []) for f in parsed_files if f.parsing_errors)

    # TODO/FIXME in original source files
    todo_files = [
        f.file_path for f in parsed_files
        if f.original_content and re.search(r'\b(TODO|FIXME|PLACEHOLDER|HACK|XXX)\b', f.original_content, re.IGNORECASE)
    ]

    lang_counts: Dict[str, int] = {}
    for f in parsed_files:
        lang_counts[f.language] = lang_counts.get(f.language, 0) + 1
    dominant_lang = max(lang_counts, key=lang_counts.get) if lang_counts else ""
    style_guide_map = {
        "Python": "PEP8", "Java": "Google Java Style Guide",
        "JavaScript": "Airbnb / ESLint", "TypeScript": "Airbnb / ESLint",
        "C#": "Microsoft C# Coding Conventions", "Go": "gofmt",
        "Ruby": "RuboCop", "PHP": "PSR-12",
    }
    style_guide = style_guide_map.get(dominant_lang, "Google Style Guide")

    api_endpoints = (
        analysis.get("apis", [])
        or (agentic.get("api_analysis", {}) or {}).get("endpoints", [])
    )
    endpoint_files = list(set(
        ep.get("file", ep.get("file_path", ""))
        for ep in api_endpoints
        if ep.get("file") or ep.get("file_path")
    ))

    # ── Context elements ───────────────────────────────────────────────────
    context_elements = db.query(ContextElement).filter(ContextElement.project_id == project_id).all()
    layers = list(set(e.layer for e in context_elements))
    high_complexity_components = [e.element_name for e in context_elements if e.complexity_level == "high"]

    # ── Validation results — pull from actual DB rows ──────────────────────
    val_results = db.query(ValidationResult).filter(ValidationResult.project_id == project_id).all()
    val_passed  = sum(1 for v in val_results if v.passed)
    val_total   = len(val_results)
    # Build a per-type lookup so the audit can surface individual scores
    val_by_type: Dict[str, Any] = {
        v.validation_type: {
            "score": v.score,
            "threshold": v.threshold,
            "passed": v.passed,
            "message": v.message,
            "evidence": v.evidence or [],
        }
        for v in val_results
    }

    # ── Stack / dependency data ────────────────────────────────────────────
    detected_stack = project.detected_stack or []
    selected_stack = project.selected_stack or {}
    frameworks_detected = parsing.get("frameworks_detected", [])
    if not frameworks_detected:
        frameworks_detected = [s.get("detected", "") for s in detected_stack if s.get("detected")]

    # ── Transformation mappings ────────────────────────────────────────────
    mappings            = project.transformation_mappings or []
    completed_mappings  = [m for m in mappings if m.get("status") in ("completed", "complete")]
    consolidated_mappings = [m for m in completed_mappings if (m.get("file_count") or 0) > 1]
    retired_mappings    = [m for m in mappings if m.get("status") in ("retired", "deprecated", "skipped")]

    # ── Business rules — use real transformation_results data ─────────────
    business_rules_total = total_functions + total_classes

    # Real counts from transformation_results stored by the pipeline
    total_output_files   = transformation_res.get("total_files_processed", 0)
    successful_tf        = transformation_res.get("successful_transformations", 0)
    failed_tf            = transformation_res.get("failed_transformations", 0)

    # Estimate mapped business rules from the ratio of successfully transformed files
    if business_rules_total > 0 and total_output_files > 0:
        ratio = successful_tf / total_output_files
        business_rules_mapped = round(business_rules_total * ratio)
    else:
        # Fall back to api_analysis endpoint count as a lower-bound proxy
        api_result_data = get_result("api_analysis")
        business_rules_mapped = len(api_result_data.get("endpoints", []))

    # ── Test scripts ───────────────────────────────────────────────────────
    test_scripts = project.test_scripts or []
    if not test_scripts:
        ts_res = get_result("test_scripts")
        test_scripts = ts_res.get("scripts", [])

    empty_test_stubs = [t for t in test_scripts if not t.get("content") or len(t.get("content", "")) < 50]

    # ── File inventory ─────────────────────────────────────────────────────
    total_legacy_files = ingestion.get("total_files") or project.total_files or 0
    # Use real output file count from transformation_results when available
    migrated_files     = successful_tf if successful_tf > 0 else (
        sum(m.get("file_count", 1) for m in completed_mappings) if completed_mappings else total_parsed
    )
    consolidated_files = len(consolidated_mappings)
    retired_files      = len(retired_mappings)

    # ── TODO markers in transformed output (from validation evidence) ──────
    # The code_quality validator stores anti_patterns evidence including TODO counts
    transformed_todo_files = todo_files  # default: original source TODOs
    tf_val = val_by_type.get("code_quality", {})
    if tf_val.get("evidence"):
        for ev in tf_val["evidence"]:
            if "TODO" in ev or "FIXME" in ev:
                # Evidence string like "42 TODO/FIXME markers in transformed code"
                transformed_todo_files = [ev]
                break

    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_path": project.path,
        "project_status": project.status,
        "validation_summary": {
            "total_checks": val_total,
            "passed_checks": val_passed,
            "failed_checks": val_total - val_passed,
            "approval_rate": round(val_passed / val_total * 100, 1) if val_total > 0 else 0.0,
            "checks_by_type": val_by_type,
        },
        "code_quality": {
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "avg_maintainability": avg_maintainability,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_parsed_files": total_parsed,
            "successful_parses": successful_parses,
            "failed_parses": failed_parses,
            "parse_success_rate": parsing.get("parse_success_rate"),
            "large_files": large_files,
            "god_class_candidates": god_class_candidates,
            "frameworks_detected": frameworks_detected,
            "total_endpoints": parsing.get("total_endpoints") or len(api_endpoints),
            "linting_violations": linting_violations,
            "style_guide": style_guide,
            # Expose real validator score for this domain
            "validator_score": val_by_type.get("code_quality", {}).get("score"),
            "validator_passed": val_by_type.get("code_quality", {}).get("passed"),
        },
        "architecture": {
            "layers": layers,
            "architecture_layers": project.architecture_layers or {},
            "high_complexity_components": high_complexity_components,
            "total_components": len(context_elements),
            "layer_count": len(layers),
            "validator_score": val_by_type.get("architecture_compliance", {}).get("score"),
            "validator_passed": val_by_type.get("architecture_compliance", {}).get("passed"),
            "validator_evidence": val_by_type.get("architecture_compliance", {}).get("evidence", []),
        },
        "dependencies": {
            "detected_stack": detected_stack,
            "selected_stack": selected_stack,
            "frameworks_detected": frameworks_detected,
            "validator_score": val_by_type.get("dependency_health", {}).get("score"),
            "validator_passed": val_by_type.get("dependency_health", {}).get("passed"),
            "validator_evidence": val_by_type.get("dependency_health", {}).get("evidence", []),
        },
        "test_coverage": {
            "test_scripts_count": len(test_scripts),
            "empty_test_stubs": empty_test_stubs,
            "total_classes": total_classes,
            # Real validation counts from DB
            "val_passed": val_passed,
            "val_total": val_total,
            "validator_score": val_by_type.get("test_coverage_readiness", {}).get("score"),
            "validator_passed": val_by_type.get("test_coverage_readiness", {}).get("passed"),
            "validator_evidence": val_by_type.get("test_coverage_readiness", {}).get("evidence", []),
        },
        "transformation": {
            "total_mappings": len(mappings),
            "completed_mappings": len(completed_mappings),
            "api_endpoints_count": len(api_endpoints),
            "api_endpoints": api_endpoints,
            "todo_files": transformed_todo_files,
            "selected_stack": selected_stack,
            "business_rules_total": business_rules_total,
            "business_rules_mapped": business_rules_mapped,
            # Real transformation stats
            "total_output_files": total_output_files,
            "successful_transformations": successful_tf,
            "failed_transformations": failed_tf,
            "validator_score": val_by_type.get("transformation_completeness", {}).get("score"),
            "validator_passed": val_by_type.get("transformation_completeness", {}).get("passed"),
            "validator_evidence": val_by_type.get("transformation_completeness", {}).get("evidence", []),
        },
        "file_coverage": {
            "total_legacy_files": total_legacy_files,
            "total_parsed_files": total_parsed,
            "migrated_files": migrated_files,
            "consolidated_files": consolidated_files,
            "retired_files": retired_files,
            "endpoint_files": endpoint_files,
            "backup_files": backup_files,
            "large_files": large_files,
            "validator_score": val_by_type.get("file_coverage", {}).get("score"),
            "validator_passed": val_by_type.get("file_coverage", {}).get("passed"),
            "validator_evidence": val_by_type.get("file_coverage", {}).get("evidence", []),
        },
    }


@router.get("/orchestrator/{project_id}/status")
async def get_orchestrator_status(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get orchestrator status for a project."""
    try:
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get orchestrator status (would be stored in database)
        status = _get_orchestrator_status(project_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get orchestrator status for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def _run_database_analysis(project_id: str, files: List[Dict[str, Any]]):
    """Background task to run database analysis."""
    try:
        logger.info(f"Starting database analysis for project {project_id}")
        
        results = database_analyzer.analyze_database_files(files)
        
        # Store results (would save to database)
        _store_database_results(project_id, results)
        
        logger.info(f"Database analysis completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Database analysis background task failed for project {project_id}: {e}")


async def _run_api_analysis(project_id: str):
    """Background task: parse the converted codebase and store API results."""
    try:
        logger.info(f"Starting API analysis for project {project_id}")
        from ..api.pipeline import _pipeline_data
        from ..services.parser import parse_files
        from ..services.analyzer import analyze_codebase
        from ..database.db import SessionLocal
        from ..models.project import AnalysisResult
        from datetime import datetime, timezone

        pipeline = _pipeline_data.get(project_id, {})
        transformed_files_dict = pipeline.get("transformed_files", {})

        # Fall back to TransformedFile DB rows if not in memory
        if not transformed_files_dict:
            from ..database.db import SessionLocal as _SL
            from ..models.project import TransformedFile as _TF
            _db = _SL()
            try:
                tf_rows = _db.query(_TF).filter(_TF.project_id == project_id).all()
                if tf_rows:
                    transformed_files_dict = {r.file_path: r.content for r in tf_rows if r.content}
            finally:
                _db.close()

        if not transformed_files_dict:
            logger.warning(f"No transformed files found for project {project_id} — skipping API analysis")
            return

        file_list = [
            {"path": path, "content": content, "language": _detect_language_from_path(path), "size": len(content)}
            for path, content in transformed_files_dict.items()
        ]

        parse_results = parse_files(file_list)
        re_analysis = analyze_codebase(parse_results, file_list)
        re_apis = re_analysis.get("apis", [])

        # Merge with original endpoints to guarantee count parity.
        # Load original endpoints from the stored analysis result.
        import os as _os
        original_apis: List[Dict] = []
        _orig_db = SessionLocal()
        try:
            _orig_res = _orig_db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id,
                AnalysisResult.result_type == "analysis",
            ).order_by(AnalysisResult.created_at.desc()).first()
            if _orig_res and _orig_res.data:
                original_apis = _orig_res.data.get("apis", [])
        finally:
            _orig_db.close()

        # Build original-file-stem → new-file-path mapping
        orig_stem_to_new: Dict[str, str] = {}
        for new_path in transformed_files_dict.keys():
            stem = _os.path.splitext(_os.path.basename(new_path))[0].lower()
            orig_stem_to_new[stem] = new_path

        def _resolve(orig_file: str) -> str:
            stem = _os.path.splitext(_os.path.basename(orig_file))[0].lower()
            return orig_stem_to_new.get(stem, orig_file)

        merged_apis = list(re_apis)
        merged_keys = {(a.get("method", "GET").upper(), a.get("path", "")) for a in re_apis}
        for orig in original_apis:
            key = (orig.get("method", "GET").upper(), orig.get("path", ""))
            if key not in merged_keys:
                merged_apis.append({
                    "method": orig.get("method", "GET"),
                    "path": orig.get("path", "/"),
                    "handler": orig.get("handler", "unknown"),
                    "type": orig.get("type", "REST"),
                    "file": _resolve(orig.get("file", "")),
                })
                merged_keys.add(key)

        apis = merged_apis

        frameworks = list(set(
            fp.get("framework", "")
            for pr in parse_results
            for fp in pr.get("framework_patterns", [])
            if fp.get("framework")
        ))

        endpoints = [
            {
                "path": api.get("path", "/"),
                "method": api.get("method", "GET"),
                "function_name": api.get("handler", "unknown"),
                "parameters": [],
                "responses": [{"status_code": 200, "description": "Success", "content_type": "application/json"}],
                "summary": f"{api.get('method', 'GET')} {api.get('path', '/')}",
                "description": f"Converted endpoint from {api.get('file', 'unknown')}",
                "tags": [api.get("type", "api")],
                "deprecated": False,
                "file_path": api.get("file", ""),
                "line_number": 0,
            }
            for api in apis
        ]

        methods_dist: Dict[str, int] = {}
        for ep in endpoints:
            m = ep.get("method", "GET")
            methods_dist[m] = methods_dist.get(m, 0) + 1

        result_data = {
            "endpoints": endpoints,
            "models": [],
            "frameworks": frameworks,
            "openapi_spec": {
                "openapi": "3.0.0",
                "info": {"title": "Converted API", "version": "1.0.0", "description": "Endpoints from the converted codebase"},
                "paths": {},
                "components": {"schemas": {}},
            },
            "statistics": {
                "total_endpoints": len(endpoints),
                "total_models": 0,
                "methods_distribution": methods_dist,
                "unique_paths": len(set(ep.get("path", "") for ep in endpoints)),
                "parameters_total": 0,
                "avg_parameters_per_endpoint": 0,
            },
            "postman_collection": {},
            "curl_examples": [],
            "conversion_summary": {
                "endpoints_converted": len(endpoints),
                "models_extracted": 0,
                "frameworks_detected": frameworks,
                "openapi_generated": False,
                "postman_collection_generated": False,
                "curl_examples_generated": False,
            },
        }

        # Persist so future requests don't need in-memory data
        db = SessionLocal()
        try:
            existing = db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id,
                AnalysisResult.result_type == "api_analysis",
            ).first()
            if existing:
                existing.data = result_data
                existing.created_at = datetime.now(timezone.utc)
            else:
                db.add(AnalysisResult(
                    project_id=project_id,
                    result_type="api_analysis",
                    data=result_data,
                    created_at=datetime.now(timezone.utc),
                ))
            db.commit()
        finally:
            db.close()

        logger.info(f"API analysis completed for project {project_id}: {len(endpoints)} endpoints found")

    except Exception as e:
        logger.error(f"API analysis background task failed for project {project_id}: {e}")


# Helper functions (would be implemented with actual database operations)
def _get_stored_database_results(project_id: str) -> Dict[str, Any]:
    """Get stored database analysis results."""
    from ..database.db import SessionLocal
    from ..models.project import AnalysisResult
    
    db = SessionLocal()
    try:
        # First try to get from agentic analysis results
        agentic_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "agentic_analysis"
        ).first()
        
        if agentic_result and agentic_result.data:
            # Check if database analysis is at the top level (new format)
            database_analysis = agentic_result.data.get("database_analysis", {})
            
            if database_analysis and database_analysis.get("schemas"):
                return database_analysis
            
            # Fallback: check inside analysis_results (old format)
            analysis_results = agentic_result.data.get("analysis_results", {})
            database_analysis = analysis_results.get("database_analysis", {})
            
            if database_analysis and database_analysis.get("schemas"):
                return database_analysis
        
        # Fallback: try to get from separate database analysis result
        db_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "database_analysis"
        ).first()
        
        if db_result and db_result.data:
            return db_result.data
        
        # Return empty structure if no data found
        return {
            "schemas": [],
            "orm_models": {},
            "analysis": {
                "total_schemas": 0,
                "total_tables": 0,
                "total_columns": 0,
                "total_indexes": 0,
                "total_foreign_keys": 0,
                "primary_database_type": "unknown",
                "relationship_analysis": {
                    "total_relationships": 0,
                    "isolated_tables": 0,
                    "highly_connected_tables": 0,
                    "relationship_graph": {}
                },
                "type_analysis": {
                    "type_distribution": {},
                    "most_common_type": "varchar",
                    "total_columns": 0
                },
                "complexity_score": 0.0
            },
            "recommendations": []
        }
    finally:
        db.close()


def _store_database_results(project_id: str, results: Dict[str, Any]):
    """Store database analysis results."""
    # This would save to database
    pass


def _get_stored_api_results(project_id: str) -> Dict[str, Any]:
    """Get API analysis results for the TRANSFORMED (new) codebase, with multi-level fallback."""
    from ..database.db import SessionLocal
    from ..models.project import AnalysisResult, Project
    from ..api.pipeline import _pipeline_data
    from ..services.parser import parse_files
    from ..services.analyzer import analyze_codebase

    def _build_response(endpoints: List[Dict], models: List[Dict], frameworks: List[str], openapi_generated: bool = False) -> Dict[str, Any]:
        total = len(endpoints)
        methods_dist: Dict[str, int] = {}
        for ep in endpoints:
            m = ep.get("method", "GET")
            methods_dist[m] = methods_dist.get(m, 0) + 1
        params_total = sum(len(ep.get("parameters", [])) for ep in endpoints)
        return {
            "endpoints": endpoints,
            "models": models,
            "frameworks": frameworks,
            "openapi_spec": {
                "openapi": "3.0.0",
                "info": {"title": "Converted API", "version": "1.0.0", "description": "API endpoints from the converted codebase"},
                "paths": {},
                "components": {"schemas": {}},
            },
            "statistics": {
                "total_endpoints": total,
                "total_models": len(models),
                "methods_distribution": methods_dist,
                "unique_paths": len(set(ep.get("path", "") for ep in endpoints)),
                "parameters_total": params_total,
                "avg_parameters_per_endpoint": params_total / max(total, 1),
            },
            "postman_collection": {},
            "curl_examples": [],
            "conversion_summary": {
                "endpoints_converted": total,
                "models_extracted": len(models),
                "frameworks_detected": frameworks,
                "openapi_generated": openapi_generated,
                "postman_collection_generated": False,
                "curl_examples_generated": False,
            },
        }

    def _apis_to_endpoints(apis: List[Dict]) -> List[Dict]:
        return [
            {
                "path": api.get("path", "/"),
                "method": api.get("method", "GET"),
                "function_name": api.get("handler", "unknown"),
                "parameters": [],
                "responses": [{"status_code": 200, "description": "Success", "content_type": "application/json"}],
                "summary": f"{api.get('method', 'GET')} {api.get('path', '/')}",
                "description": f"API endpoint from {api.get('file', 'unknown file')}",
                "tags": [api.get("type", "api")],
                "deprecated": False,
                "file_path": api.get("file", ""),
                "line_number": 0,
            }
            for api in apis
        ]

    # ── 1. Parse transformed files directly from in-memory pipeline data ──
    # This is the most accurate source — the actual converted codebase files
    pipeline = _pipeline_data.get(project_id, {})
    transformed_files_dict: Dict[str, str] = pipeline.get("transformed_files", {})

    # ── 1b. If not in memory, load from TransformedFile DB rows ──────────────
    if not transformed_files_dict:
        db_check = SessionLocal()
        try:
            from ..models.project import TransformedFile as _TF2
            tf_rows2 = db_check.query(_TF2).filter(_TF2.project_id == project_id).all()
            if tf_rows2:
                transformed_files_dict = {r.file_path: r.content for r in tf_rows2 if r.content}
        finally:
            db_check.close()

    if transformed_files_dict:
        try:
            import os as _os2
            file_list = [
                {"path": path, "content": content, "language": _detect_language_from_path(path), "size": len(content)}
                for path, content in transformed_files_dict.items()
            ]
            parse_results = parse_files(file_list)
            re_analysis = analyze_codebase(parse_results, file_list)
            re_apis = re_analysis.get("apis", [])

            # Load original endpoints for merge
            _orig_apis: List[Dict] = []
            _orig_db2 = SessionLocal()
            try:
                _orig_r = _orig_db2.query(AnalysisResult).filter(
                    AnalysisResult.project_id == project_id,
                    AnalysisResult.result_type == "analysis",
                ).order_by(AnalysisResult.created_at.desc()).first()
                if _orig_r and _orig_r.data:
                    _orig_apis = _orig_r.data.get("apis", [])
            finally:
                _orig_db2.close()

            # Build stem → new path mapping
            _stem_map: dict = {}
            for _np in transformed_files_dict.keys():
                _s = _os2.path.splitext(_os2.path.basename(_np))[0].lower()
                _stem_map[_s] = _np

            def _res2(f: str) -> str:
                _s = _os2.path.splitext(_os2.path.basename(f))[0].lower()
                return _stem_map.get(_s, f)

            merged = list(re_apis)
            merged_keys = {(a.get("method", "GET").upper(), a.get("path", "")) for a in re_apis}
            for orig in _orig_apis:
                key = (orig.get("method", "GET").upper(), orig.get("path", ""))
                if key not in merged_keys:
                    merged.append({
                        "method": orig.get("method", "GET"),
                        "path": orig.get("path", "/"),
                        "handler": orig.get("handler", "unknown"),
                        "type": orig.get("type", "REST"),
                        "file": _res2(orig.get("file", "")),
                    })
                    merged_keys.add(key)

            apis = merged
            if apis:
                frameworks = list(set(
                    fp.get("framework", "")
                    for pr in parse_results
                    for fp in pr.get("framework_patterns", [])
                    if fp.get("framework")
                ))
                return _build_response(_apis_to_endpoints(apis), [], frameworks)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Direct transformed file parse failed: {e}")

    db = SessionLocal()
    try:
        # ── 2. comparative_analysis.transformed_analysis — post-transformation orchestrator output ──
        comparative = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "comparative_analysis",
        ).order_by(AnalysisResult.created_at.desc()).first()

        if comparative and comparative.data:
            transformed_api = (
                comparative.data.get("transformed_analysis", {}).get("api_analysis")
                or comparative.data.get("transformed_analysis", {}).get("analysis_results", {}).get("api_analysis", {})
            )
            if transformed_api and transformed_api.get("endpoints"):
                return _build_response(
                    transformed_api["endpoints"],
                    transformed_api.get("models", []),
                    transformed_api.get("frameworks", []),
                    bool(transformed_api.get("openapi_spec")),
                )

        # ── 3. Dedicated api_analysis result (may be from transformed codebase) ──
        api_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "api_analysis",
        ).order_by(AnalysisResult.created_at.desc()).first()
        if api_result and api_result.data and api_result.data.get("endpoints"):
            return api_result.data

        # ── 4. agentic_analysis — may contain api_analysis from original or transformed ──
        agentic_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "agentic_analysis",
        ).order_by(AnalysisResult.created_at.desc()).first()

        if agentic_result and agentic_result.data:
            api_analysis = (
                agentic_result.data.get("api_analysis")
                or agentic_result.data.get("analysis_results", {}).get("api_analysis", {})
            )
            if api_analysis and api_analysis.get("endpoints"):
                return _build_response(
                    api_analysis["endpoints"],
                    api_analysis.get("models", []),
                    api_analysis.get("frameworks", []),
                    bool(api_analysis.get("openapi_spec")),
                )

        # ── 5. Regular analysis result (detected_apis from original parse) ──
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "analysis",
        ).order_by(AnalysisResult.created_at.desc()).first()
        if analysis_result and analysis_result.data:
            apis = analysis_result.data.get("apis", [])
            if apis:
                return _build_response(_apis_to_endpoints(apis), [], [])

        # ── 6. Project.detected_apis column ──
        project = db.query(Project).filter(Project.id == project_id).first()
        if project and project.detected_apis:
            return _build_response(_apis_to_endpoints(project.detected_apis), [], [])

        return _build_response([], [], [])
    finally:
        db.close()


def _detect_language_from_path(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.java': 'Java', '.cs': 'C#', '.cpp': 'C++', '.c': 'C',
        '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go', '.rs': 'Rust',
        '.kt': 'Kotlin', '.swift': 'Swift', '.sql': 'SQL',
    }
    import os
    _, ext = os.path.splitext(file_path.lower())
    return ext_map.get(ext, 'Unknown')


def _store_api_results(project_id: str, results: Dict[str, Any]):
    """Store API analysis results."""
    # This would save to database
    pass


def _get_orchestrator_status(project_id: str) -> Dict[str, Any]:
    """Get orchestrator status from stored analysis results."""
    from ..database.db import SessionLocal
    from ..models.project import AnalysisResult, ValidationResult

    db = SessionLocal()
    try:
        agentic = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.result_type == "agentic_analysis",
        ).order_by(AnalysisResult.created_at.desc()).first()

        val_results = db.query(ValidationResult).filter(
            ValidationResult.project_id == project_id
        ).all()

        val_total  = len(val_results)
        val_passed = sum(1 for v in val_results if v.passed)
        approval_rate = round(val_passed / val_total * 100, 1) if val_total > 0 else 0.0

        if val_total == 0:
            validation_status = "pending"
        elif approval_rate >= 70:
            validation_status = "approved"
        elif approval_rate >= 40:
            validation_status = "requires_review"
        else:
            validation_status = "rejected"

        if agentic and agentic.data:
            data = agentic.data
            return {
                "project_id": project_id,
                "current_step": "completed",
                "completed_steps": data.get("agentic_summary", {}).get("total_steps_completed", 0),
                "status": data.get("orchestration_status", "completed"),
                "confidence_scores": data.get("confidence_scores", {}),
                "validation_status": validation_status,
                "approval_rate": approval_rate,
                "val_passed": val_passed,
                "val_total": val_total,
            }

        return {
            "project_id": project_id,
            "current_step": "not_started",
            "completed_steps": 0,
            "status": "idle",
            "confidence_scores": {},
            "validation_status": validation_status,
            "approval_rate": approval_rate,
            "val_passed": val_passed,
            "val_total": val_total,
        }
    finally:
        db.close()


@router.get("/functional-preservation/{project_id}")
async def get_functional_preservation(project_id: str, db: Session = Depends(get_db)):
    """Return the functional preservation report for a project."""
    from ..models.project import AnalysisResult

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id,
        AnalysisResult.result_type == "functional_preservation",
    ).order_by(AnalysisResult.created_at.desc()).first()

    if not result or not result.data:
        return {
            "project_id": project_id,
            "available": False,
            "message": "Functional preservation report not yet available. Run the transformation pipeline first.",
        }

    return {"project_id": project_id, "available": True, **result.data}

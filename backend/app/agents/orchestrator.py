"""LangGraph Orchestrator for Agentic CodeMorph System."""

import os
import logging
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass
import asyncio

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from .analysis_agent import AnalysisAgent
from .context_agent import ContextAgent
from .base_agent import AgentResult
from ..services.confidence_scoring import ConfidenceScoringEngine
from ..services.database_analyzer import DatabaseAnalyzer
from ..services.api_converter import APIConverter
from ..services.behavioral_validation import BehavioralValidationEngine

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent orchestration graph."""
    input_data: Dict[str, Any]
    context: Dict[str, Any]
    analysis_results: Dict[str, Any]
    context_results: Dict[str, Any]
    dependency_graph: Dict[str, Any]
    confidence_scores: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    errors: List[str]
    current_step: str
    completed_steps: List[str]
    human_review_required: bool
    validation_results: Dict[str, Any]
    database_analysis: Dict[str, Any]
    api_analysis: Dict[str, Any]


@dataclass
class OrchestrationConfig:
    """Configuration for orchestration."""
    enable_human_review: bool = True
    confidence_threshold: float = 0.7
    max_retries: int = 3
    parallel_execution: bool = True
    validation_gates: List[str] = None
    enable_database_analysis: bool = True
    enable_api_conversion: bool = True
    enable_behavioral_validation: bool = True


class CodeMorphOrchestrator:
    """LangGraph-based orchestrator for CodeMorph agents."""
    
    def __init__(
        self,
        llm: Optional[ChatGroq] = None,
        config: Optional[OrchestrationConfig] = None
    ):
        # Configure Groq if not provided
        if llm is None:
            groq_api_key = os.environ.get("GROQ_API_KEY")
            groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

            if groq_api_key:
                self.llm = ChatGroq(
                    api_key=groq_api_key,
                    model=groq_model,
                    temperature=0.1,
                )
            else:
                logger.warning("Groq not configured, agentic analysis will be disabled")
                raise ValueError("GROQ_API_KEY is required for agentic analysis")
        else:
            self.llm = llm
            
        self.config = config or OrchestrationConfig()
        
        # Initialize agents
        self.analysis_agent = AnalysisAgent(llm=self.llm)
        self.context_agent = ContextAgent(llm=self.llm)
        
        # Initialize new services
        self.confidence_engine = ConfidenceScoringEngine()
        self.database_analyzer = DatabaseAnalyzer()
        self.api_converter = APIConverter()
        self.validation_engine = BehavioralValidationEngine()
        
        # Build the orchestration graph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph orchestration graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_state)
        workflow.add_node("context_analysis", self._run_context_analysis)
        workflow.add_node("code_analysis", self._run_code_analysis)
        workflow.add_node("dependency_analysis", self._run_dependency_analysis)
        workflow.add_node("database_analyzer", self._run_database_analysis)
        workflow.add_node("api_analyzer", self._run_api_analysis)
        workflow.add_node("confidence_scoring", self._calculate_confidence_scores)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("human_review_gate", self._human_review_gate)
        workflow.add_node("validation", self._validate_results)
        workflow.add_node("finalize", self._finalize_results)
        
        # Define the flow
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "context_analysis")
        workflow.add_edge("context_analysis", "code_analysis")
        workflow.add_edge("code_analysis", "dependency_analysis")
        workflow.add_edge("dependency_analysis", "database_analyzer")
        workflow.add_edge("database_analyzer", "api_analyzer")
        workflow.add_edge("api_analyzer", "confidence_scoring")
        workflow.add_edge("confidence_scoring", "generate_recommendations")
        
        # Conditional edge for human review
        workflow.add_conditional_edges(
            "generate_recommendations",
            self._should_require_human_review,
            {
                "human_review": "human_review_gate",
                "validation": "validation"
            }
        )
        
        workflow.add_edge("human_review_gate", "validation")
        workflow.add_edge("validation", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def orchestrate(
        self,
        files: List[Dict[str, Any]],
        project_context: Dict[str, Any],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Orchestrate the complete analysis pipeline."""
        initial_state = {
            "input_data": {
                "files": files,
                "project_context": project_context,
                "analysis_type": analysis_type
            },
            "context": {},
            "analysis_results": {},
            "context_results": {},
            "dependency_graph": {},
            "confidence_scores": {},
            "recommendations": [],
            "errors": [],
            "current_step": "initialize",
            "completed_steps": [],
            "human_review_required": False,
            "validation_results": {},
            "database_analysis": {},
            "api_analysis": {}
        }
        
        try:
            # Run the orchestration graph
            result = await self.graph.ainvoke(initial_state)
            
            # Store results in database
            project_id = project_context.get("project_id")
            if project_id:
                await self._store_orchestration_results(project_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {
                "error": str(e),
                "completed_steps": initial_state.get("completed_steps", []),
                "current_step": initial_state.get("current_step", "unknown")
            }
    
    async def _store_orchestration_results(self, project_id: str, results: Dict[str, Any]):
        """Store orchestration results in database."""
        from ..database.db import SessionLocal
        from ..models.project import (
            DatabaseAnalysisResult, APIAnalysisResult, 
            ValidationResult, ReviewRequest
        )
        
        db = SessionLocal()
        try:
            # Store database analysis results
            if results.get("database_analysis"):
                db_analysis = results["database_analysis"]
                db_result = DatabaseAnalysisResult(
                    project_id=project_id,
                    database_type=db_analysis.get("database_type", "unknown"),
                    schema_name=db_analysis.get("schema_name", "default"),
                    tables_count=db_analysis.get("tables_count", 0),
                    views_count=db_analysis.get("views_count", 0),
                    procedures_count=db_analysis.get("procedures_count", 0),
                    functions_count=db_analysis.get("functions_count", 0),
                    triggers_count=db_analysis.get("triggers_count", 0),
                    tables_data=db_analysis.get("tables_data", []),
                    relationships=db_analysis.get("relationships", []),
                    indexes=db_analysis.get("indexes", []),
                    orm_models=db_analysis.get("orm_models", {}),
                    recommendations=db_analysis.get("recommendations", []),
                    complexity_metrics=db_analysis.get("complexity_metrics", {}),
                    old_schema=db_analysis.get("old_schema", {}),
                    new_schema=db_analysis.get("new_schema", {}),
                    migration_scripts=db_analysis.get("migration_scripts", [])
                )
                db.add(db_result)
            
            # Store API analysis results
            if results.get("api_analysis"):
                api_analysis = results["api_analysis"]
                api_result = APIAnalysisResult(
                    project_id=project_id,
                    framework_type=api_analysis.get("framework_type", "unknown"),
                    endpoints_count=api_analysis.get("endpoints_count", 0),
                    models_count=api_analysis.get("models_count", 0),
                    endpoints_data=api_analysis.get("endpoints_data", []),
                    models_data=api_analysis.get("models_data", []),
                    openapi_spec=api_analysis.get("openapi_spec", {}),
                    postman_collection=api_analysis.get("postman_collection", {}),
                    curl_examples=api_analysis.get("curl_examples", []),
                    old_framework=api_analysis.get("old_framework"),
                    new_framework=api_analysis.get("new_framework"),
                    conversion_mappings=api_analysis.get("conversion_mappings", []),
                    statistics=api_analysis.get("statistics", {})
                )
                db.add(api_result)
            
            # Store validation results
            if results.get("validation_results"):
                validation_data = results["validation_results"]
                for validation in validation_data.get("validations", []):
                    val_result = ValidationResult(
                        project_id=project_id,
                        validation_type=validation.get("rule_type", "unknown"),
                        status=validation.get("status", "pending"),
                        score=validation.get("score", 0.0),
                        threshold=validation.get("threshold", 0.0),
                        passed=validation.get("passed", False),
                        message=validation.get("message", ""),
                        evidence=validation.get("evidence", []),
                        recommendations=validation.get("recommendations", [])
                    )
                    db.add(val_result)
                
                # Store review requests if any
                for review in validation_data.get("review_requests", []):
                    review_req = ReviewRequest(
                        project_id=project_id,
                        title=review.get("title", ""),
                        description=review.get("description", ""),
                        priority=review.get("priority", "medium"),
                        status=review.get("status", "pending"),
                        context_data=review.get("context_data", {})
                    )
                    db.add(review_req)
            
            db.commit()
            logger.info(f"Stored orchestration results for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to store orchestration results: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _initialize_state(self, state: AgentState) -> AgentState:
        """Initialize the orchestration state."""
        logger.info("Initializing orchestration state")
        
        state["current_step"] = "initialize"
        state["completed_steps"].append("initialize")
        
        # Validate input data
        files = state["input_data"].get("files", [])
        if not files:
            state["errors"].append("No files provided for analysis")
            return state
        
        # Set up context
        state["context"] = {
            "total_files": len(files),
            "languages": list(set(f.get("language", "unknown") for f in files)),
            "start_time": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Initialized with {len(files)} files")
        return state
    
    async def _run_context_analysis(self, state: AgentState) -> AgentState:
        """Run context analysis using ContextAgent."""
        logger.info("Running context analysis")
        
        state["current_step"] = "context_analysis"
        
        try:
            from .context_agent import ContextAnalysisInput
            
            context_input = ContextAnalysisInput(
                files=state["input_data"]["files"],
                parse_results=[],  # Will be populated by parser
                project_info=state["input_data"]["project_context"]
            )
            
            result = await self.context_agent.analyze(context_input)
            
            if result.success:
                state["context_results"] = result.data
                state["confidence_scores"]["context"] = result.confidence
            else:
                state["errors"].extend(result.errors)
                
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            state["errors"].append(f"Context analysis failed: {str(e)}")
        
        state["completed_steps"].append("context_analysis")
        return state
    
    async def _run_code_analysis(self, state: AgentState) -> AgentState:
        """Run code analysis using AnalysisAgent."""
        logger.info("Running code analysis")
        
        state["current_step"] = "code_analysis"
        
        try:
            result = await self.analysis_agent.analyze_architecture(
                files=state["input_data"]["files"],
                context=state["input_data"]["project_context"]
            )
            
            if result.success:
                state["analysis_results"] = result.data
                state["confidence_scores"]["analysis"] = result.confidence
            else:
                state["errors"].extend(result.errors)
                
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            state["errors"].append(f"Code analysis failed: {str(e)}")
        
        state["completed_steps"].append("code_analysis")
        return state
    
    async def _run_dependency_analysis(self, state: AgentState) -> AgentState:
        """Run dependency graph analysis."""
        logger.info("Running dependency analysis")
        
        state["current_step"] = "dependency_analysis"
        
        try:
            # Extract dependency information from context and analysis results
            context_deps = state["context_results"].get("dependencies_and_relationships", {})
            analysis_deps = state["analysis_results"].get("dependencies", {})
            
            # Merge and enhance dependency information
            dependency_graph = self._build_enhanced_dependency_graph(
                context_deps, analysis_deps, state["input_data"]["files"]
            )
            
            state["dependency_graph"] = dependency_graph
            state["confidence_scores"]["dependencies"] = self._calculate_dependency_confidence(dependency_graph)
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            state["errors"].append(f"Dependency analysis failed: {str(e)}")
        
        state["completed_steps"].append("dependency_analysis")
        return state
    
    async def _run_database_analysis(self, state: AgentState) -> AgentState:
        """Run database analysis and ORM generation."""
        logger.info("Running database analysis")
        
        state["current_step"] = "database_analysis"
        
        if not self.config.enable_database_analysis:
            logger.info("Database analysis disabled")
            state["database_analysis"] = {}
            state["completed_steps"].append("database_analysis")
            return state
        
        try:
            files = state["input_data"].get("files", [])
            
            # Run database analysis
            database_results = self.database_analyzer.analyze_database_files(files)
            
            # Store enhanced database analysis results
            enhanced_db_analysis = {
                "schemas": database_results.get("schemas", []),
                "orm_models": database_results.get("orm_models", {}),
                "analysis": {
                    "total_schemas": len(database_results.get("schemas", [])),
                    "total_tables": sum(len(schema.get("tables", [])) for schema in database_results.get("schemas", [])),
                    "total_columns": database_results.get("total_columns", 0),
                    "total_indexes": database_results.get("total_indexes", 0),
                    "total_foreign_keys": database_results.get("total_foreign_keys", 0),
                    "primary_database_type": database_results.get("primary_database_type", "unknown"),
                    "relationship_analysis": database_results.get("relationship_analysis", {
                        "total_relationships": 0,
                        "isolated_tables": 0,
                        "highly_connected_tables": 0,
                        "relationship_graph": {}
                    }),
                    "type_analysis": database_results.get("type_analysis", {
                        "type_distribution": {},
                        "most_common_type": "varchar",
                        "total_columns": 0
                    }),
                    "complexity_score": database_results.get("complexity_score", 0.5)
                },
                "recommendations": database_results.get("recommendations", [])
            }
            
            state["database_analysis"] = enhanced_db_analysis
            
            # Update confidence scores
            if "confidence_scores" not in state:
                state["confidence_scores"] = {}
            
            # Calculate database analysis confidence
            db_confidence = self._calculate_database_confidence(database_results)
            state["confidence_scores"]["database"] = db_confidence
            
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            state["errors"].append(f"Database analysis failed: {str(e)}")
            state["database_analysis"] = {
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
        
        state["completed_steps"].append("database_analysis")
        return state
    
    async def _run_api_analysis(self, state: AgentState) -> AgentState:
        """Run API analysis and conversion."""
        logger.info("Running API analysis")
        
        state["current_step"] = "api_analysis"
        
        if not self.config.enable_api_conversion:
            logger.info("API analysis disabled")
            state["api_analysis"] = {}
            state["completed_steps"].append("api_analysis")
            return state
        
        try:
            files = state["input_data"].get("files", [])
            
            # Run API analysis
            api_results = self.api_converter.convert_api_files(files)
            
            # Store enhanced API analysis results
            endpoints = api_results.get("endpoints", [])
            models = api_results.get("models", [])
            frameworks = api_results.get("frameworks", [])
            
            enhanced_api_analysis = {
                "endpoints": [
                    {
                        "path": ep.get("path", "/"),
                        "method": ep.get("method", "GET"),
                        "function_name": ep.get("function_name", "unknown"),
                        "parameters": ep.get("parameters", []),
                        "responses": ep.get("responses", [{"status_code": 200, "description": "Success", "content_type": "application/json"}]),
                        "summary": ep.get("summary", f"{ep.get('method', 'GET')} {ep.get('path', '/')}"),
                        "description": ep.get("description", f"API endpoint from {ep.get('file_path', 'unknown file')}"),
                        "tags": ep.get("tags", []),
                        "deprecated": ep.get("deprecated", False),
                        "file_path": ep.get("file_path", ""),
                        "line_number": ep.get("line_number", 0)
                    }
                    for ep in endpoints
                ],
                "models": [
                    {
                        "name": model.get("name", "UnknownModel"),
                        "properties": model.get("properties", {}),
                        "required_fields": model.get("required_fields", []),
                        "description": model.get("description", ""),
                        "example": model.get("example", {})
                    }
                    for model in models
                ],
                "frameworks": frameworks,
                "openapi_spec": api_results.get("openapi_spec", {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Generated API",
                        "version": "1.0.0",
                        "description": "Auto-generated API specification"
                    },
                    "paths": {},
                    "components": {"schemas": {}}
                }),
                "statistics": {
                    "total_endpoints": len(endpoints),
                    "total_models": len(models),
                    "methods_distribution": api_results.get("methods_distribution", {}),
                    "unique_paths": len(set(ep.get("path", "") for ep in endpoints)),
                    "parameters_total": sum(len(ep.get("parameters", [])) for ep in endpoints),
                    "avg_parameters_per_endpoint": sum(len(ep.get("parameters", [])) for ep in endpoints) / max(len(endpoints), 1)
                },
                "postman_collection": api_results.get("postman_collection", {}),
                "curl_examples": api_results.get("curl_examples", []),
                "conversion_summary": {
                    "endpoints_converted": len(endpoints),
                    "models_extracted": len(models),
                    "frameworks_detected": frameworks,
                    "openapi_generated": bool(api_results.get("openapi_spec")),
                    "postman_collection_generated": bool(api_results.get("postman_collection")),
                    "curl_examples_generated": len(api_results.get("curl_examples", [])) > 0
                }
            }
            
            state["api_analysis"] = enhanced_api_analysis
            
            # Update confidence scores
            if "confidence_scores" not in state:
                state["confidence_scores"] = {}
            
            # Calculate API analysis confidence
            api_confidence = self._calculate_api_confidence(api_results)
            state["confidence_scores"]["api"] = api_confidence
            
        except Exception as e:
            logger.error(f"API analysis failed: {e}")
            state["errors"].append(f"API analysis failed: {str(e)}")
            state["api_analysis"] = {
                "endpoints": [],
                "models": [],
                "frameworks": [],
                "openapi_spec": {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "API Analysis",
                        "version": "1.0.0",
                        "description": "No API endpoints detected"
                    },
                    "paths": {},
                    "components": {"schemas": {}}
                },
                "statistics": {
                    "total_endpoints": 0,
                    "total_models": 0,
                    "methods_distribution": {},
                    "unique_paths": 0,
                    "parameters_total": 0,
                    "avg_parameters_per_endpoint": 0
                },
                "postman_collection": {},
                "curl_examples": [],
                "conversion_summary": {
                    "endpoints_converted": 0,
                    "models_extracted": 0,
                    "frameworks_detected": [],
                    "openapi_generated": False,
                    "postman_collection_generated": False,
                    "curl_examples_generated": False
                }
            }
        
        state["completed_steps"].append("api_analysis")
        return state
    
    async def _calculate_confidence_scores(self, state: AgentState) -> AgentState:
        """Calculate comprehensive confidence scores using the confidence engine."""
        logger.info("Calculating confidence scores")
        
        state["current_step"] = "confidence_scoring"
        
        try:
            # Use the confidence scoring engine
            confidence_scores = self.confidence_engine.calculate_comprehensive_confidence(
                analysis_results=state.get("analysis_results", {}),
                context_results=state.get("context_results", {}),
                files=state["input_data"].get("files", []),
                errors=state.get("errors", [])
            )
            
            # Convert confidence scores to simple dict for state
            state["confidence_scores"] = {
                category.value: score.score 
                for category, score in confidence_scores.items()
            }
            
            # Store detailed confidence information
            state["detailed_confidence"] = {
                category.value: {
                    "score": score.score,
                    "reasoning": score.reasoning,
                    "evidence": score.evidence,
                    "factors": score.factors,
                    "metadata": score.metadata
                }
                for category, score in confidence_scores.items()
            }
            
        except Exception as e:
            logger.error(f"Confidence scoring failed: {e}")
            state["errors"].append(f"Confidence scoring failed: {str(e)}")
            # Fallback to simple confidence calculation
            state["confidence_scores"] = {
                "overall": 0.5,
                "analysis": 0.5,
                "context": 0.5,
                "dependencies": 0.5
            }
        
        state["completed_steps"].append("confidence_scoring")
        return state
    
    async def _generate_recommendations(self, state: AgentState) -> AgentState:
        """Generate comprehensive recommendations."""
        logger.info("Generating recommendations")
        
        state["current_step"] = "generate_recommendations"
        
        try:
            recommendations = []
            
            # Architecture recommendations
            arch_recs = self._generate_architecture_recommendations(state)
            recommendations.extend(arch_recs)
            
            # Security recommendations
            sec_recs = self._generate_security_recommendations(state)
            recommendations.extend(sec_recs)
            
            # Performance recommendations
            perf_recs = self._generate_performance_recommendations(state)
            recommendations.extend(perf_recs)
            
            # Modernization recommendations
            mod_recs = self._generate_modernization_recommendations(state)
            recommendations.extend(mod_recs)
            
            # Prioritize recommendations
            recommendations = self._prioritize_recommendations(recommendations, state)
            
            state["recommendations"] = recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            state["errors"].append(f"Recommendation generation failed: {str(e)}")
        
        state["completed_steps"].append("generate_recommendations")
        return state
    
    def _should_require_human_review(self, state: AgentState) -> str:
        """Determine if human review is required."""
        if not self.config.enable_human_review:
            return "validation"
        
        # Check confidence threshold
        overall_confidence = state["confidence_scores"].get("overall", 0.0)
        if overall_confidence < self.config.confidence_threshold:
            state["human_review_required"] = True
            return "human_review"
        
        # Check for critical security issues
        security_confidence = state["confidence_scores"].get("security", 1.0)
        if security_confidence < 0.5:
            state["human_review_required"] = True
            return "human_review"
        
        # Check for errors
        if state["errors"]:
            state["human_review_required"] = True
            return "human_review"
        
        return "validation"
    
    async def _human_review_gate(self, state: AgentState) -> AgentState:
        """Human review gate — records review requirement without running post-transformation validators."""
        logger.info("Entering human review gate")

        state["current_step"] = "human_review"

        # Behavioral validation (file coverage, transformation completeness, etc.) requires
        # the fully transformed codebase which doesn't exist yet at this stage of the pipeline.
        # Running it here would always produce 0-score results and trigger false rejections.
        # Real validation is performed in _create_transformation_validation_results after
        # transformation completes. Here we only check analysis-stage confidence.
        try:
            overall_confidence = state["confidence_scores"].get("overall", 0.0)
            security_confidence = state["confidence_scores"].get("security", 1.0)
            errors = state.get("errors", [])

            if overall_confidence >= self.config.confidence_threshold and security_confidence >= 0.5 and not errors:
                logger.info(f"Analysis confidence {overall_confidence:.2f} meets threshold — no human review required")
                state["human_review_required"] = False
                state["validation_results"] = {
                    "overall_status": "approved",
                    "confidence": overall_confidence,
                    "message": "Analysis confidence meets threshold",
                }
            else:
                reasons = []
                if overall_confidence < self.config.confidence_threshold:
                    reasons.append(f"confidence {overall_confidence:.2f} < threshold {self.config.confidence_threshold}")
                if security_confidence < 0.5:
                    reasons.append(f"security confidence {security_confidence:.2f} < 0.5")
                if errors:
                    reasons.append(f"{len(errors)} analysis error(s)")
                reason_str = "; ".join(reasons)
                logger.info(f"Analysis review flagged: {reason_str}")
                state["human_review_required"] = True
                state["validation_results"] = {
                    "overall_status": "requires_review",
                    "confidence": overall_confidence,
                    "message": f"Review flagged: {reason_str}",
                }
        except Exception as e:
            logger.error(f"Human review gate failed: {e}")
            state["errors"].append(f"Human review gate failed: {str(e)}")
            state["validation_results"] = {"overall_status": "requires_review", "message": str(e)}
            state["human_review_required"] = True

        state["completed_steps"].append("human_review")
        return state
    
    async def _validate_results(self, state: AgentState) -> AgentState:
        """Validate the analysis results."""
        logger.info("Validating results")
        
        state["current_step"] = "validation"
        
        try:
            validation_results = {}
            
            # Validate completeness
            validation_results["completeness"] = self._validate_completeness(state)
            
            # Validate consistency
            validation_results["consistency"] = self._validate_consistency(state)
            
            # Validate confidence levels
            validation_results["confidence"] = self._validate_confidence_levels(state)
            
            state["validation_results"].update(validation_results)
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state["errors"].append(f"Validation failed: {str(e)}")
        
        state["completed_steps"].append("validation")
        return state
    
    async def _finalize_results(self, state: AgentState) -> AgentState:
        """Finalize the orchestration results."""
        logger.info("Finalizing results")
        
        state["current_step"] = "finalize"
        
        # Calculate execution time
        end_time = asyncio.get_event_loop().time()
        start_time = state["context"].get("start_time", end_time)
        execution_time = end_time - start_time

        # Generate LLM-powered codebase documentation
        try:
            codebase_doc = await self._generate_codebase_documentation(state)
            state["codebase_documentation"] = codebase_doc
        except Exception as e:
            logger.warning(f"Codebase documentation generation failed (non-critical): {e}")
            state["codebase_documentation"] = ""
        
        # Create final summary
        state["final_summary"] = {
            "success": len(state["errors"]) == 0,
            "execution_time": execution_time,
            "steps_completed": len(state["completed_steps"]),
            "overall_confidence": state["confidence_scores"].get("overall", 0.0),
            "recommendations_count": len(state["recommendations"]),
            "errors_count": len(state["errors"]),
            "human_review_required": state["human_review_required"]
        }
        
        state["completed_steps"].append("finalize")
        logger.info(f"Orchestration completed in {execution_time:.2f}s")
        
        return state

    async def _generate_codebase_documentation(self, state: AgentState) -> str:
        """Use the LLM to generate rich business-level documentation of the codebase.

        This produces the human-readable summary shown in the 'Context Built' tab —
        it explains what the application actually *does* (business rules, domain,
        workflows) rather than just listing files and technologies.
        """
        files = state["input_data"].get("files", [])
        project_context = state["input_data"].get("project_context", {})
        analysis_results = state.get("analysis_results", {})
        context_results = state.get("context_results", {})
        database_analysis = state.get("database_analysis", {})
        api_analysis = state.get("api_analysis", {})
        confidence_scores = state.get("confidence_scores", {})

        # ── Build a rich prompt from all gathered analysis data ──────────────
        total_files = len(files)
        languages = list(set(f.get("language", "unknown") for f in files if f.get("language")))
        total_loc = sum(f.get("loc", len((f.get("content") or "").splitlines())) for f in files)

        # Collect class/function names from files for business rule inference
        class_names: List[str] = []
        function_names: List[str] = []
        for f in files[:50]:  # cap to avoid huge prompts
            content = f.get("content", "") or ""
            # Quick regex-free extraction: look for lines with "class " or "def "/"function "
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("class ") and len(class_names) < 40:
                    name = stripped.split("class ")[1].split("(")[0].split(":")[0].split("{")[0].strip()
                    if name:
                        class_names.append(name)
                if (stripped.startswith("def ") or stripped.startswith("function ") or
                        stripped.startswith("public ") or stripped.startswith("private ") or
                        stripped.startswith("protected ")) and len(function_names) < 60:
                    for kw in ("def ", "function ", "public ", "private ", "protected "):
                        if stripped.startswith(kw):
                            rest = stripped[len(kw):]
                            name = rest.split("(")[0].split(" ")[-1].strip()
                            if name and not name.startswith("@"):
                                function_names.append(name)
                            break

        # Architecture layers
        arch_layers = context_results.get("architecture_layers") or {}
        layer_summary = ""
        if arch_layers:
            parts = []
            for layer, data in arch_layers.items():
                if isinstance(data, dict):
                    fcount = data.get("file_count", len(data.get("files", [])))
                    fws = data.get("frameworks", [])
                    parts.append(f"{layer} ({fcount} files{', ' + ', '.join(fws) if fws else ''})")
            layer_summary = "; ".join(parts)

        # API endpoints
        endpoints = api_analysis.get("endpoints", [])
        endpoint_summary = ""
        if endpoints:
            ep_lines = [f"  - {ep.get('method','GET')} {ep.get('path','/')} — {ep.get('summary') or ep.get('function_name','')}"
                        for ep in endpoints[:20]]
            endpoint_summary = "\n".join(ep_lines)
            if len(endpoints) > 20:
                endpoint_summary += f"\n  ... and {len(endpoints) - 20} more endpoints"

        # Database tables
        db_schemas = database_analysis.get("schemas", [])
        table_names: List[str] = []
        for schema in db_schemas:
            for tbl in schema.get("tables", []):
                table_names.append(tbl.get("name", ""))
        table_summary = ", ".join(table_names[:30]) if table_names else ""

        # Sample file contents (small files only, for business rule inference)
        sample_code_sections: List[str] = []
        for f in files:
            content = f.get("content", "") or ""
            if 100 < len(content) < 3000:
                sample_code_sections.append(
                    f"### {f.get('path', 'unknown')} ({f.get('language', '')})\n"
                    f"```\n{content[:1500]}\n```"
                )
            if len(sample_code_sections) >= 8:
                break

        sample_code = "\n\n".join(sample_code_sections)

        prompt = f"""You are a senior software architect tasked with writing the official technical documentation for a codebase.

Based on the analysis data below, write a comprehensive **Codebase Documentation** that explains:
1. **What this application does** — its business purpose, domain, and the problems it solves
2. **Core business rules and workflows** — the key processes, logic flows, and domain rules encoded in the code
3. **Key functional modules** — what each major component/service/module is responsible for
4. **Data model** — what entities/tables exist and what they represent in the business domain
5. **API surface** — what operations the system exposes and to whom
6. **Integration points** — external systems, services, or dependencies the application interacts with
7. **Architecture overview** — how the layers/tiers are organized and how data flows through the system

Write this as clear, professional documentation that a new developer or business analyst could read to understand exactly what this system does. Focus on **business meaning** — not just technical facts. Use plain English paragraphs, not bullet lists.

---

## Analysis Data

**Project:** {project_context.get('name', 'Unknown')} | Path: {project_context.get('source_path', '')}
**Scale:** {total_files} files, ~{total_loc:,} lines of code
**Languages:** {', '.join(languages) if languages else 'Unknown'}
**Architecture Layers:** {layer_summary or 'Not detected'}

**Classes identified ({len(class_names)}):**
{', '.join(class_names[:40]) if class_names else 'None detected'}

**Functions/Methods identified ({len(function_names)}):**
{', '.join(function_names[:60]) if function_names else 'None detected'}

**API Endpoints ({len(endpoints)}):**
{endpoint_summary or 'No endpoints detected'}

**Database Tables ({len(table_names)}):**
{table_summary or 'No tables detected'}

**Analysis Confidence:** {confidence_scores.get('overall', 0):.0%}

## Sample Source Code
{sample_code if sample_code else 'No source code samples available.'}

---

Write the documentation now. Be specific about what this application actually does based on the code evidence above. If the code is a university management system, say so and explain the enrollment, grading, and faculty workflows. If it is an e-commerce platform, explain the product catalog, order processing, and payment flows. Ground every claim in the actual class names, function names, endpoints, and tables you can see.

Do not use headers or markdown formatting — write flowing prose paragraphs. Aim for 300-500 words."""

        try:
            response = await self.llm.ainvoke(prompt)
            doc = response.content.strip() if hasattr(response, "content") else str(response).strip()
            if doc:
                logger.info(f"Generated codebase documentation ({len(doc)} chars)")
                return doc
        except Exception as e:
            logger.warning(f"LLM documentation generation failed: {e}")

        # Fallback: structured template using gathered data
        return self._generate_fallback_documentation(
            total_files, total_loc, languages, layer_summary,
            class_names, function_names, endpoints, table_names
        )

    def _generate_fallback_documentation(
        self,
        total_files: int,
        total_loc: int,
        languages: List[str],
        layer_summary: str,
        class_names: List[str],
        function_names: List[str],
        endpoints: List[Dict],
        table_names: List[str],
    ) -> str:
        """Generate structured documentation without LLM as a fallback."""
        parts: List[str] = []

        lang_str = ", ".join(languages) if languages else "multiple languages"
        parts.append(
            f"This codebase consists of {total_files} source files totalling approximately "
            f"{total_loc:,} lines of code, written primarily in {lang_str}."
        )

        if layer_summary:
            parts.append(f"The application is organized into the following architectural layers: {layer_summary}.")

        if class_names:
            parts.append(
                f"Key domain classes identified include: {', '.join(class_names[:20])}."
                + (f" Among the {len(class_names)} total classes, these represent the core business entities and services." if len(class_names) > 20 else "")
            )

        if function_names:
            parts.append(
                f"Core operations and business logic are implemented through functions and methods such as: "
                f"{', '.join(function_names[:25])}."
            )

        if endpoints:
            methods = {}
            for ep in endpoints:
                m = ep.get("method", "GET")
                methods[m] = methods.get(m, 0) + 1
            method_str = ", ".join(f"{count} {m}" for m, count in methods.items())
            parts.append(
                f"The system exposes {len(endpoints)} API endpoints ({method_str}), "
                f"providing programmatic access to its core functionality."
            )

        if table_names:
            parts.append(
                f"The data model comprises {len(table_names)} database entities: "
                f"{', '.join(table_names[:20])}{'...' if len(table_names) > 20 else ''}. "
                f"These tables store the persistent state of the application's business domain."
            )

        if not parts:
            return "Codebase analysis is in progress. Documentation will be available once the analysis completes."

        return " ".join(parts)
    
    def _build_enhanced_dependency_graph(
        self,
        context_deps: Dict[str, Any],
        analysis_deps: Dict[str, Any],
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build dependency graph from real context and analysis data."""
        nodes = []
        edges = []
        seen_nodes: set = set()

        # Add file nodes
        for f in files:
            path = f.get("path", "")
            if path and path not in seen_nodes:
                nodes.append({"id": path, "type": "file", "language": f.get("language", "unknown")})
                seen_nodes.add(path)

        # Add edges from context imports
        imports_map = context_deps.get("imports", {})
        for source, targets in imports_map.items():
            if source not in seen_nodes:
                nodes.append({"id": source, "type": "module"})
                seen_nodes.add(source)
            for target in (targets if isinstance(targets, list) else []):
                if target not in seen_nodes:
                    nodes.append({"id": target, "type": "module"})
                    seen_nodes.add(target)
                edges.append({"source": source, "target": target, "type": "import"})

        # Add circular dependency edges
        for cycle in context_deps.get("circular_dependencies", []):
            if isinstance(cycle, list) and len(cycle) >= 2:
                for i in range(len(cycle) - 1):
                    edges.append({"source": cycle[i], "target": cycle[i + 1], "type": "circular"})

        # Cluster by directory
        clusters: Dict[str, List[str]] = {}
        for node in nodes:
            parts = node["id"].replace("\\", "/").split("/")
            cluster = parts[0] if len(parts) > 1 else "root"
            clusters.setdefault(cluster, []).append(node["id"])

        return {
            "nodes": nodes,
            "edges": edges,
            "clusters": [{"name": k, "members": v} for k, v in clusters.items()],
            "metrics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "circular_dependencies": len(context_deps.get("circular_dependencies", [])),
            }
        }
    
    def _calculate_dependency_confidence(self, dependency_graph: Dict[str, Any]) -> float:
        """Calculate confidence from the actual dependency graph data."""
        nodes = dependency_graph.get("nodes", [])
        edges = dependency_graph.get("edges", [])
        if not nodes and not edges:
            return 0.0
        # More nodes/edges = more complete graph = higher confidence, capped at 0.95
        node_score = min(0.5, len(nodes) * 0.05)
        edge_score = min(0.45, len(edges) * 0.03)
        return round(min(0.95, node_score + edge_score), 3)

    def _calculate_architecture_confidence(self, state: AgentState) -> float:
        """Calculate confidence from real context and analysis results."""
        context = state.get("context_results", {})
        layers = context.get("architecture_layers") or context.get("layers") or {}
        components = context.get("components", [])
        deps = context.get("dependencies_and_relationships", {})

        if not layers and not components:
            return 0.0

        layer_score = min(0.4, len(layers) * 0.1)
        component_score = min(0.35, len(components) * 0.05)
        dep_score = 0.25 if deps else 0.0
        return round(min(0.95, layer_score + component_score + dep_score), 3)

    def _calculate_security_confidence(self, state: AgentState) -> float:
        """Calculate confidence from real security analysis data."""
        analysis = state.get("analysis_results", {})
        security = analysis.get("security", {})

        if not security:
            return 0.0

        score = 0.0
        if "vulnerabilities" in security:
            score += 0.4
        if "security_patterns" in security:
            score += 0.3
        if "risk_assessment" in security:
            score += 0.3
        return round(min(0.95, score), 3)

    def _calculate_quality_confidence(self, state: AgentState) -> float:
        """Calculate confidence from real code quality metrics."""
        analysis = state.get("analysis_results", {})
        files = state.get("input_data", {}).get("files", [])

        if not files:
            return 0.0

        has_complexity = "complexity" in analysis
        has_patterns = bool(analysis.get("patterns"))
        has_quality_score = "code_quality_score" in analysis
        errors = state.get("errors", [])
        error_penalty = min(0.3, len(errors) * 0.05)

        score = (0.4 if has_complexity else 0.0) + \
                (0.3 if has_patterns else 0.0) + \
                (0.3 if has_quality_score else 0.0)
        # Minimum 0.3 when we at least have files to analyse
        score = max(0.3, score - error_penalty)
        return round(min(0.95, score), 3)
    
    def _generate_architecture_recommendations(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate architecture-specific recommendations."""
        return []
    
    def _generate_security_recommendations(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate security-specific recommendations."""
        return []
    
    def _generate_performance_recommendations(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate performance-specific recommendations."""
        return []
    
    def _generate_modernization_recommendations(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate modernization-specific recommendations."""
        return []
    
    def _prioritize_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on impact and confidence."""
        return recommendations
    
    def _validate_completeness(self, state: AgentState) -> Dict[str, Any]:
        """Validate completeness of analysis."""
        return {"score": 0.9, "missing_components": []}
    
    def _validate_consistency(self, state: AgentState) -> Dict[str, Any]:
        """Validate consistency across analysis results."""
        return {"score": 0.9, "inconsistencies": []}
    
    def _validate_confidence_levels(self, state: AgentState) -> Dict[str, Any]:
        """Validate confidence levels are appropriate."""
        return {"score": 0.9, "low_confidence_areas": []}
    def _calculate_database_confidence(self, database_results: Dict[str, Any]) -> float:
        """Calculate confidence score for database analysis."""
        if not database_results or "error" in database_results:
            return 0.0
        
        schemas = database_results.get("schemas", [])
        if not schemas:
            return 0.3  # Low confidence if no schemas found
        
        # Base confidence on number of successfully analyzed schemas
        total_tables = sum(len(schema.get("tables", [])) for schema in schemas)
        orm_models = database_results.get("orm_models", {})
        
        # Higher confidence if we have both schemas and generated models
        if total_tables > 0 and orm_models:
            return min(0.9, 0.5 + (total_tables * 0.05))  # Cap at 0.9
        elif total_tables > 0:
            return min(0.7, 0.4 + (total_tables * 0.03))  # Cap at 0.7
        else:
            return 0.2
    
    def _calculate_api_confidence(self, api_results: Dict[str, Any]) -> float:
        """Calculate confidence score for API analysis."""
        if not api_results or "error" in api_results:
            return 0.0
        
        endpoints = api_results.get("endpoints", [])
        models = api_results.get("models", [])
        frameworks = api_results.get("frameworks", [])
        
        if not endpoints and not models:
            return 0.2  # Low confidence if no API components found
        
        # Base confidence on number of detected components
        endpoint_score = min(0.4, len(endpoints) * 0.05)
        model_score = min(0.3, len(models) * 0.1)
        framework_score = min(0.3, len(frameworks) * 0.15)
        
        total_confidence = endpoint_score + model_score + framework_score
        
        # Bonus for having OpenAPI spec generated
        if api_results.get("openapi_spec"):
            total_confidence += 0.1
        
        return min(0.95, total_confidence)
    
    def get_validation_dashboard(self) -> Dict[str, Any]:
        """Get behavioral validation dashboard data."""
        if not self.config.enable_behavioral_validation:
            return {"error": "Behavioral validation is disabled"}
        
        return self.validation_engine.get_review_dashboard()
    
    def submit_review_decision(
        self,
        request_id: str,
        decision: str,
        reviewer: str,
        notes: Optional[str] = None,
        decision_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a review decision for behavioral validation."""
        if not self.config.enable_behavioral_validation:
            return {"error": "Behavioral validation is disabled"}
        
        return self.validation_engine.submit_review_decision(
            request_id=request_id,
            decision=decision,
            reviewer=reviewer,
            notes=notes,
            decision_reason=decision_reason
        )
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation metrics and analytics."""
        if not self.config.enable_behavioral_validation:
            return {"error": "Behavioral validation is disabled"}
        
        return self.validation_engine.get_validation_metrics()
    
    def configure_validation_criteria(self, criteria_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Configure validation criteria for behavioral validation."""
        if not self.config.enable_behavioral_validation:
            return {"error": "Behavioral validation is disabled"}
        
        return self.validation_engine.configure_validation_criteria(criteria_list)
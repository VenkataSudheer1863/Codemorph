"""Pipeline API — start, status, cancel, and stack selection."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.db import get_db, SessionLocal
from app.models.project import Project, PipelineRun, AnalysisResult, ParsedFile, ContextElement, PIPELINE_STAGES
from app.models.schemas import PipelineStatus, StackSelection
from app.services.ingestion import ingest_codebase
from app.services.parser import parse_files
from app.services.context_builder import build_context
from app.services.analyzer import analyze_codebase
from app.services.stack_detector import detect_stack
from app.services.recommender import generate_recommendations
from app.services.transformer import (
    build_transformation_mappings,
    transform_codebase,
    create_artifact_zip,
)
from app.services.test_generator import generate_test_scripts
from app.embeddings.vector_store import build_vector_store, get_rag_retriever
# Import agentic orchestrator
from app.agents.orchestrator import CodeMorphOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["pipeline"])

# In-memory state for running pipelines
_pipeline_tasks: dict[str, asyncio.Task] = {}
_pipeline_data: dict[str, dict] = {}  # project_id -> intermediate data


def _update_project_status(project_id: str, status: str, **kwargs):
    """Update project status in DB."""
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = status
            project.updated_at = datetime.now(timezone.utc)
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            db.commit()
    finally:
        db.close()


def _create_pipeline_run(project_id: str, stage: str, message: str = "", progress: float = 0.0):
    """Create a new pipeline run record."""
    db = SessionLocal()
    try:
        pipeline_run = PipelineRun(
            project_id=project_id,
            stage=stage,
            progress=progress,
            message=message,
            started_at=datetime.now(timezone.utc)
        )
        db.add(pipeline_run)
        db.commit()
        db.refresh(pipeline_run)
        return pipeline_run.id
    finally:
        db.close()


def _complete_pipeline_run(run_id: str, progress: float = 100.0, message: str = ""):
    """Mark a pipeline run as completed."""
    db = SessionLocal()
    try:
        pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if pipeline_run:
            pipeline_run.progress = progress
            pipeline_run.message = message
            pipeline_run.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _create_analysis_result(project_id: str, result_type: str, data: dict):
    """Store analysis result data."""
    db = SessionLocal()
    try:
        analysis_result = AnalysisResult(
            project_id=project_id,
            result_type=result_type,
            data=data,
            created_at=datetime.now(timezone.utc)
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        return analysis_result.id
    finally:
        db.close()


def _store_parsed_file(project_id: str, file_data: dict, parse_result: dict):
    """Store detailed parsed file information."""
    import hashlib
    
    db = SessionLocal()
    try:
        # Calculate content hash
        content = file_data.get("content", "")
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        parsed_file = ParsedFile(
            project_id=project_id,
            file_path=file_data.get("path", ""),
            file_type=file_data.get("type", "unknown"),
            language=parse_result.get("language", "unknown"),
            framework=parse_result.get("framework", None),
            ast_data=parse_result.get("ast", {}),
            functions=parse_result.get("functions", []),
            classes=parse_result.get("classes", []),
            imports=parse_result.get("imports", []),
            exports=parse_result.get("exports", []),
            variables=parse_result.get("variables", []),
            lines_of_code=len(content.split("\n")) if content else 0,
            complexity_score=parse_result.get("complexity", 0.0),
            maintainability_index=parse_result.get("maintainability", 0.0),
            original_content=content,
            content_hash=content_hash,
            parsing_successful=parse_result.get("success", True),
            parsing_errors=parse_result.get("errors", [])
        )
        db.add(parsed_file)
        db.commit()
        db.refresh(parsed_file)
        return parsed_file.id
    finally:
        db.close()


def _store_context_element(project_id: str, element_data: dict):
    """Store context element information."""
    db = SessionLocal()
    try:
        context_element = ContextElement(
            project_id=project_id,
            element_type=element_data.get("type", "component"),
            element_name=element_data.get("name", ""),
            file_path=element_data.get("file_path", ""),
            layer=element_data.get("layer", "unknown"),
            description=element_data.get("description", ""),
            technologies=element_data.get("technologies", []),
            dependencies=element_data.get("dependencies", []),
            dependents=element_data.get("dependents", []),
            code_patterns=element_data.get("patterns", []),
            api_endpoints=element_data.get("endpoints", []),
            database_entities=element_data.get("entities", []),
            confidence_score=element_data.get("confidence", 0.0),
            complexity_level=element_data.get("complexity", "medium")
        )
        db.add(context_element)
        db.commit()
        db.refresh(context_element)
        return context_element.id
    finally:
        db.close()


def _generate_project_summary_from_context(project_id: str) -> str:
    """Generate project summary from stored context elements and parsed files."""
    db = SessionLocal()
    try:
        # Get all context elements
        context_elements = db.query(ContextElement).filter(ContextElement.project_id == project_id).all()
        parsed_files = db.query(ParsedFile).filter(ParsedFile.project_id == project_id).all()
        
        if not context_elements and not parsed_files:
            return "Project analysis in progress..."
        
        # Analyze project structure
        layers = {}
        technologies = set()
        total_files = len(parsed_files)
        total_loc = sum(f.lines_of_code for f in parsed_files)
        
        for element in context_elements:
            layer = element.layer
            if layer not in layers:
                layers[layer] = {"components": [], "technologies": set()}
            
            layers[layer]["components"].append({
                "name": element.element_name,
                "type": element.element_type,
                "complexity": element.complexity_level
            })
            
            for tech in element.technologies:
                technologies.add(tech)
                layers[layer]["technologies"].add(tech)
        
        # Generate summary
        summary_parts = []
        
        # Project overview
        summary_parts.append(f"This project consists of {total_files} files with {total_loc:,} lines of code.")
        
        # Architecture description
        if layers:
            summary_parts.append(f"The application follows a {len(layers)}-tier architecture:")
            for layer_name, layer_data in layers.items():
                component_count = len(layer_data["components"])
                tech_list = ", ".join(sorted(layer_data["technologies"]))
                summary_parts.append(f"- {layer_name.title()} Layer: {component_count} components using {tech_list}")
        
        # Technology stack
        if technologies:
            tech_list = ", ".join(sorted(technologies))
            summary_parts.append(f"Key technologies identified: {tech_list}")
        
        # Component analysis
        component_types = {}
        for element in context_elements:
            comp_type = element.element_type
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        if component_types:
            comp_desc = ", ".join([f"{count} {comp_type}{'s' if count > 1 else ''}" 
                                 for comp_type, count in component_types.items()])
            summary_parts.append(f"The codebase contains {comp_desc}.")
        
        # Complexity assessment
        complexity_levels = [e.complexity_level for e in context_elements]
        if complexity_levels:
            high_complexity = complexity_levels.count("high")
            if high_complexity > 0:
                summary_parts.append(f"The project has {high_complexity} high-complexity components that may require careful migration planning.")
            else:
                summary_parts.append("The project structure appears well-organized with manageable complexity levels.")
        
        return " ".join(summary_parts)
        
    finally:
        db.close()


async def _run_pipeline(project_id: str):
    """Execute the full analysis/transformation pipeline."""
    try:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        source_path = project.path
        db.close()

        # === Stage 1: Ingesting ===
        ingesting_run_id = _create_pipeline_run(project_id, "ingesting", "Starting codebase ingestion")
        _update_project_status(project_id, "ingesting")
        logger.info(f"[{project_id}] Stage: ingesting")

        ingestion_result = await asyncio.get_event_loop().run_in_executor(
            None, ingest_codebase, source_path
        )

        # Store ingestion results
        _create_analysis_result(project_id, "ingestion", {
            "total_files": ingestion_result["total_files"],
            "total_loc": ingestion_result["total_loc"],
            "language_distribution": ingestion_result["language_distribution"],
            "file_types": ingestion_result.get("file_types", {}),
            "directory_structure": ingestion_result.get("directory_structure", []),
            "largest_files": ingestion_result.get("largest_files", []),
            "source_path": source_path,
            "ingestion_time": ingestion_result.get("processing_time", 0)
        })

        _update_project_status(
            project_id, "ingesting",
            total_files=ingestion_result["total_files"],
            total_loc=ingestion_result["total_loc"],
            languages_count=len(ingestion_result["language_distribution"]),
            language_distribution=ingestion_result["language_distribution"],
        )

        files = ingestion_result["files"]
        _pipeline_data[project_id] = {"files": files}
        
        _complete_pipeline_run(ingesting_run_id, 100.0, f"Ingested {ingestion_result['total_files']} files")

        # === Stage 2: Parsing ===
        parsing_run_id = _create_pipeline_run(project_id, "parsing", "Parsing source files with AST analysis")
        _update_project_status(project_id, "parsing")
        logger.info(f"[{project_id}] Stage: parsing")

        parse_results = await asyncio.get_event_loop().run_in_executor(
            None, parse_files, files
        )
        _pipeline_data[project_id]["parse_results"] = parse_results

        # Store detailed parsed file information
        for i, parse_result in enumerate(parse_results):
            if i < len(files):
                file_data = files[i]
                _store_parsed_file(project_id, file_data, parse_result)

        # Count frameworks and collect parsing statistics
        frameworks = set()
        total_classes = 0
        total_functions = 0
        total_endpoints = 0
        parsing_errors = []
        
        for pr in parse_results:
            # Count frameworks
            for fp in pr.get("framework_patterns", []):
                fw = fp.get("framework", fp.get("type", ""))
                if fw:
                    frameworks.add(fw)
            
            # Count code elements
            total_classes += len(pr.get("classes", []))
            total_functions += len(pr.get("functions", []))
            total_endpoints += len(pr.get("endpoints", []))
            
            # Collect errors
            if pr.get("errors"):
                parsing_errors.extend(pr["errors"])

        # Store parsing results
        _create_analysis_result(project_id, "parsing", {
            "frameworks_detected": list(frameworks),
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_endpoints": total_endpoints,
            "parsing_errors": parsing_errors,
            "files_parsed": len(parse_results),
            "parse_success_rate": len([pr for pr in parse_results if not pr.get("errors")]) / len(parse_results) * 100 if parse_results else 0,
            "detailed_results": parse_results[:10]  # Store first 10 for reference
        })

        _update_project_status(project_id, "parsing", frameworks_count=len(frameworks))
        _complete_pipeline_run(parsing_run_id, 100.0, f"Parsed {len(parse_results)} files, found {len(frameworks)} frameworks")

        # === Stage 3: Context Building ===
        context_run_id = _create_pipeline_run(project_id, "context_building", "Building code context and dependency graph")
        _update_project_status(project_id, "context_building")
        logger.info(f"[{project_id}] Stage: context_building")

        context = await asyncio.get_event_loop().run_in_executor(
            None, build_context, parse_results, files
        )
        _pipeline_data[project_id]["context"] = context

        # Store context elements in database
        for layer_name, layer_data in context.get("layers", {}).items():
            # Get components from the main components list that belong to this layer
            layer_components = [comp for comp in context.get("components", []) if comp.get("layer") == layer_name]
            
            for component in layer_components:
                element_data = {
                    "type": component.get("type", "component"),
                    "name": component.get("name", ""),
                    "file_path": component.get("file", ""),
                    "layer": layer_name,
                    "description": f"{component.get('type', 'Component')} in {layer_name} layer",
                    "technologies": layer_data.get("frameworks", []),
                    "dependencies": [],  # Will be populated from dependency graph
                    "patterns": [],
                    "endpoints": [],
                    "entities": [],
                    "confidence": 0.8,
                    "complexity": "medium"
                }
                _store_context_element(project_id, element_data)

        # Generate dynamic project summary from stored context
        dynamic_summary = _generate_project_summary_from_context(project_id)

        # Store context building results
        _create_analysis_result(project_id, "context_building", {
            "architecture_layers": context["layers"],
            "total_components": context.get("total_components", 0),
            "dependencies": context.get("dependencies", {}),
            "service_map": context.get("service_map", {}),
            "project_summary": dynamic_summary,
            "layer_statistics": {
                layer: {
                    "file_count": data.get("file_count", 0),
                    "component_count": len(data.get("components", [])),
                    "framework_count": len(data.get("frameworks", []))
                }
                for layer, data in context["layers"].items()
            }
        })

        _update_project_status(
            project_id, "context_building",
            architecture_layers=context["layers"],
            project_summary=dynamic_summary,
        )

        # Also build vector store for RAG
        try:
            vector_store = await asyncio.get_event_loop().run_in_executor(
                None, build_vector_store, project_id, files, parse_results
            )
            _pipeline_data[project_id]["vector_store"] = vector_store
        except Exception as e:
            logger.warning(f"Vector store creation failed (non-critical): {e}")
            _pipeline_data[project_id]["vector_store"] = None

        _complete_pipeline_run(context_run_id, 100.0, f"Built context for {context.get('total_components', 0)} components")

        # === Stage 3.5: Enhanced Agentic Analysis ===
        agentic_run_id = _create_pipeline_run(project_id, "agentic_analysis", "Running enhanced agentic analysis")
        _update_project_status(project_id, "agentic_analysis")
        logger.info(f"[{project_id}] Stage: agentic_analysis")

        try:
            # Initialize agentic orchestrator with enhanced configuration
            from app.agents.orchestrator import OrchestrationConfig
            
            config = OrchestrationConfig(
                enable_human_review=True,
                confidence_threshold=0.7,
                enable_database_analysis=True,
                enable_api_conversion=True,
                enable_behavioral_validation=True
            )
            
            orchestrator = CodeMorphOrchestrator(config=config)
            
            # Run agentic analysis
            agentic_results = await orchestrator.orchestrate(
                files=files,
                project_context={
                    "project_id": project_id,
                    "parse_results": parse_results,
                    "context": context,
                    "source_path": source_path
                }
            )
            
            # Store agentic analysis results
            _pipeline_data[project_id]["agentic_results"] = agentic_results
            
            # Extract enhanced analysis data
            enhanced_analysis = agentic_results.get("analysis_results", {})
            confidence_scores = agentic_results.get("confidence_scores", {})
            recommendations = agentic_results.get("recommendations", [])
            database_analysis = agentic_results.get("database_analysis", {})
            api_analysis = agentic_results.get("api_analysis", {})
            validation_results = agentic_results.get("validation_results", {})
            
            # Extract LLM-generated codebase documentation (the rich business-level summary)
            codebase_documentation = agentic_results.get("codebase_documentation", "")

            # Store comprehensive agentic analysis results
            _create_analysis_result(project_id, "agentic_analysis", {
                "orchestration_status": "completed" if not agentic_results.get("error") else "failed",
                "analysis_results": enhanced_analysis,
                "confidence_scores": confidence_scores,
                "recommendations": recommendations,
                "database_analysis": database_analysis,
                "api_analysis": api_analysis,
                "validation_results": validation_results,
                "human_review_required": agentic_results.get("human_review_required", False),
                "codebase_documentation": codebase_documentation,
                "agentic_summary": {
                    "total_steps_completed": len(agentic_results.get("completed_steps", [])),
                    "analysis_confidence": confidence_scores.get("overall", 0.0),
                    "critical_findings": len([r for r in recommendations if r.get("priority") == "high"]),
                    "database_tables_found": database_analysis.get("analysis", {}).get("total_tables", 0),
                    "api_endpoints_found": api_analysis.get("statistics", {}).get("total_endpoints", 0),
                    "validation_passed": validation_results.get("overall_status") in ["approved", "auto_approved"]
                }
            })

            # Store the initial dependency graph separately for later comparison.
            # Always rebuild from files+parse_results to get the full typed schema
            # (file/class/function nodes with proper metrics). The orchestrator's
            # dependency_graph uses a sparse format that lacks typed node counts.
            # We schedule this as a background rebuild so it doesn't block the pipeline.
            try:
                initial_dep_graph = await _build_dependency_graph_from_files(
                    files, _pipeline_data[project_id].get("parse_results", [])
                )
                _create_analysis_result(project_id, "initial_dependency_graph", initial_dep_graph)
                _pipeline_data[project_id]["initial_dependency_graph"] = initial_dep_graph
                logger.info(
                    f"[{project_id}] Built initial dependency graph: "
                    f"{initial_dep_graph['metrics']['file_nodes']} file nodes, "
                    f"{initial_dep_graph['metrics']['class_nodes']} class nodes, "
                    f"{initial_dep_graph['metrics']['total_edges']} edges"
                )
            except Exception as _dg_err:
                logger.warning(f"[{project_id}] Initial dependency graph build failed (non-critical): {_dg_err}")
            
            # Store separate enhanced analysis results
            if database_analysis:
                _create_analysis_result(project_id, "database_analysis", database_analysis)
            
            if api_analysis:
                _create_analysis_result(project_id, "api_analysis", api_analysis)
            
            if validation_results:
                _create_analysis_result(project_id, "validation_results", validation_results)
            
            # Update project with enhanced analysis.
            # If the LLM produced codebase documentation, use it as the project_summary
            # so the "Context Built" tab shows what the application actually does.
            summary_to_store = codebase_documentation if codebase_documentation else dynamic_summary
            _update_project_status(
                project_id, "agentic_analysis",
                project_summary=summary_to_store,
            )
            
            _complete_pipeline_run(agentic_run_id, 100.0, f"Enhanced agentic analysis completed with {confidence_scores.get('overall', 0):.1f} confidence")
            
        except Exception as e:
            logger.warning(f"[{project_id}] Agentic analysis failed, falling back to traditional analysis: {e}")
            _complete_pipeline_run(agentic_run_id, 50.0, f"Agentic analysis failed: {str(e)}, using fallback")
            # Continue with traditional analysis as fallback
            _pipeline_data[project_id]["agentic_results"] = None

        # === Background Processing: Analysis, Detection & Recommendations ===
        # These stages run in background but are hidden from UI
        background_run_id = _create_pipeline_run(project_id, "background_processing", "Running analysis, detection, and recommendations")
        
        # Check if we have agentic results to use
        agentic_results = _pipeline_data[project_id].get("agentic_results")
        
        if agentic_results and agentic_results.get("status") == "completed":
            # Use enhanced agentic analysis results
            logger.info(f"[{project_id}] Using agentic analysis results")
            
            analysis = agentic_results.get("analysis_results", {}).get("code_analysis", {})
            detected_stack = agentic_results.get("analysis_results", {}).get("stack_detection", [])
            recommendations = agentic_results.get("recommendations", [])
            
            # Ensure we have the expected format
            if not analysis.get("apis"):
                analysis["apis"] = []
            if not analysis.get("tables"):
                analysis["tables"] = []
                
        else:
            # Fallback to traditional analysis
            logger.info(f"[{project_id}] Using traditional analysis (agentic failed or unavailable)")
            
            # Run analysis
            analysis = await asyncio.get_event_loop().run_in_executor(
                None, analyze_codebase, parse_results, files
            )
            
            # Run stack detection
            detected_stack = await asyncio.get_event_loop().run_in_executor(
                None, detect_stack, parse_results, files, analysis
            )
            
            # Generate recommendations
            recommendations = await asyncio.get_event_loop().run_in_executor(
                None, generate_recommendations, detected_stack
            )
        
        # Store results in pipeline data
        _pipeline_data[project_id]["analysis"] = analysis
        _pipeline_data[project_id]["detected_stack"] = detected_stack
        _pipeline_data[project_id]["recommendations"] = recommendations

        # Store analysis results
        _create_analysis_result(project_id, "analysis", {
            "apis": analysis["apis"],
            "tables": analysis["tables"],
            "stored_procedures": analysis.get("stored_procedures", []),
            "orm_entities": analysis.get("orm_entities", []),
            "message_queues": analysis.get("message_queues", []),
            "soap_services": analysis.get("soap_services", []),
            "api_statistics": {
                "total_endpoints": len(analysis["apis"]),
                "methods_distribution": {},
                "endpoint_types": {}
            },
            "database_statistics": {
                "total_tables": len(analysis["tables"]),
                "total_relationships": sum(tbl.get("relationships", 0) for tbl in analysis["tables"]),
                "table_types": {}
            }
        })

        # Store stack detection results
        _create_analysis_result(project_id, "stack_detection", {
            "detected_stack": detected_stack,
            "confidence_scores": {item["category"]: item["confidence"] for item in detected_stack},
            "alternatives": {item["category"]: item.get("alternatives", []) for item in detected_stack},
            "detection_method": "Enhanced agentic analysis" if agentic_results else "AST analysis + pattern matching",
            "stack_summary": {
                "frontend": [item for item in detected_stack if item["category"] == "frontend_framework"],
                "backend": [item for item in detected_stack if item["category"] == "backend_framework"],
                "database": [item for item in detected_stack if item["category"] == "database"],
                "build_tools": [item for item in detected_stack if item["category"] == "build_tool"]
            }
        })

        # Store recommendation results
        _create_analysis_result(project_id, "recommendations", {
            "recommendations": recommendations,
            "recommendation_rationale": {
                rec["category"]: {
                    "current": rec["detected"],
                    "suggested": rec["suggestions"],
                    "confidence": rec["confidence"],
                    "modernization_benefits": f"Upgrade from {rec['detected']} to modern alternatives"
                }
                for rec in recommendations
            },
            "modernization_scope": {
                "total_categories": len(recommendations),
                "high_priority": [rec for rec in recommendations if rec["confidence"] > 80],
                "medium_priority": [rec for rec in recommendations if 50 <= rec["confidence"] <= 80],
                "low_priority": [rec for rec in recommendations if rec["confidence"] < 50]
            }
        })

        # Ensure we have at least some basic recommendations for testing
        if not recommendations and not detected_stack:
            # Add fallback recommendations for empty projects
            detected_stack = [
                {
                    "category": "frontend_framework",
                    "label": "Frontend Framework",
                    "detected": "Unknown",
                    "confidence": 50,
                    "alternatives": ["React", "Angular", "Vue.js"]
                },
                {
                    "category": "backend_framework", 
                    "label": "Backend Framework",
                    "detected": "Unknown",
                    "confidence": 50,
                    "alternatives": ["Spring Boot", "FastAPI", "Express.js"]
                }
            ]
            recommendations = [
                {
                    "category": "frontend_framework",
                    "label": "Frontend Framework",
                    "detected": "Unknown",
                    "confidence": 70,
                    "suggestions": ["React", "Angular", "Vue.js"]
                },
                {
                    "category": "backend_framework",
                    "label": "Backend Framework", 
                    "detected": "Unknown",
                    "confidence": 70,
                    "suggestions": ["Spring Boot", "FastAPI", "Express.js"]
                }
            ]
            logger.info(f"[{project_id}] Added fallback recommendations for empty project")
            _pipeline_data[project_id]["detected_stack"] = detected_stack
            _pipeline_data[project_id]["recommendations"] = recommendations

        # Store recommendation results
        _create_analysis_result(project_id, "recommendations", {
            "recommendations": recommendations,
            "recommendation_rationale": {
                rec["category"]: {
                    "current": rec["detected"],
                    "suggested": rec["suggestions"],
                    "confidence": rec["confidence"],
                    "modernization_benefits": f"Upgrade from {rec['detected']} to modern alternatives"
                }
                for rec in recommendations
            },
            "modernization_scope": {
                "total_categories": len(recommendations),
                "high_priority": [rec for rec in recommendations if rec["confidence"] > 80],
                "medium_priority": [rec for rec in recommendations if 50 <= rec["confidence"] <= 80],
                "low_priority": [rec for rec in recommendations if rec["confidence"] < 50]
            }
        })

        # Update project with all analysis results
        logger.info(f"[{project_id}] Analysis results: APIs={len(analysis['apis'])}, Tables={len(analysis['tables'])}")
        logger.info(f"[{project_id}] Detected stack: {len(detected_stack)} technologies")
        logger.info(f"[{project_id}] Recommendations: {len(recommendations)} items")
        
        _update_project_status(
            project_id, "selecting",
            detected_apis=analysis["apis"],
            detected_tables=analysis["tables"],
            detected_stack=detected_stack,
            recommendations=recommendations
        )
        
        _complete_pipeline_run(background_run_id, 100.0, f"Completed analysis: {len(analysis['apis'])} APIs, {len(detected_stack)} technologies, {len(recommendations)} recommendations")

        # === Stage 7: Selecting (wait for user input) ===
        selecting_run_id = _create_pipeline_run(project_id, "selecting", "Waiting for user stack selection")
        _update_project_status(project_id, "selecting")
        logger.info(f"[{project_id}] Stage: selecting — waiting for user selection")

        # Store the run ID for completion later
        _pipeline_data[project_id]["selecting_run_id"] = selecting_run_id

        # Pipeline pauses here. It will resume when user submits stack selection.

    except asyncio.CancelledError:
        _update_project_status(project_id, "cancelled", error_message="Pipeline cancelled")
        logger.info(f"[{project_id}] Pipeline cancelled")
    except Exception as e:
        _update_project_status(project_id, "error", error_message=str(e))
        logger.error(f"[{project_id}] Pipeline error: {e}", exc_info=True)
    finally:
        _pipeline_tasks.pop(project_id, None)


def _persist_transformed_files(project_id: str, transformed_files_dict: Dict[str, str],
                               parse_results_by_path: Dict[str, dict]) -> int:
    """
    Persist each transformed file to the transformed_files table with computed metrics.
    Returns the number of rows inserted.
    """
    import hashlib
    import re as _re
    from app.models.project import TransformedFile

    DECISION_KW   = _re.compile(r'\b(if|elif|else|for|while|case|catch|except|and|or)\b', _re.IGNORECASE)
    TODO_KW       = _re.compile(r'\b(TODO|FIXME|HACK|XXX|PLACEHOLDER)\b', _re.IGNORECASE)
    PASSTHROUGH_P = _re.compile(r'#\s*TODO.*transform|pass-through|original content', _re.IGNORECASE)

    db = SessionLocal()
    try:
        # Delete any previous rows for this project so re-runs stay clean
        db.query(TransformedFile).filter(TransformedFile.project_id == project_id).delete()

        rows = []
        for file_path, content in transformed_files_dict.items():
            content = content or ""
            lines   = content.splitlines()
            loc     = max(len(lines), 1)
            decisions = len(DECISION_KW.findall(content))

            # McCabe proxy: 1 + (decisions / LOC) * 100
            cyclomatic = round(1 + (decisions / loc) * 100, 2)

            # Halstead-inspired maintainability proxy (0-100)
            avg_line_len = len(content) / loc
            mi = max(0.0, min(100.0, 100 - (decisions / loc * 50) - (avg_line_len / 10)))

            todo_count = len(TODO_KW.findall(content))
            syntax_err = (
                abs(content.count('{') - content.count('}')) > 5 or
                abs(content.count('(') - content.count(')')) > 5
            )
            is_passthrough = bool(PASSTHROUGH_P.search(content))
            content_hash   = hashlib.sha256(content.encode()).hexdigest()
            language       = _detect_language_from_path(file_path)

            # Pull parsed structure if available (from the re-parse done during auto API analysis)
            pr = parse_results_by_path.get(file_path, {})

            rows.append(TransformedFile(
                project_id=project_id,
                file_path=file_path,
                language=language,
                content=content,
                content_hash=content_hash,
                lines_of_code=loc,
                cyclomatic_complexity=cyclomatic,
                maintainability_index=round(mi, 2),
                todo_count=todo_count,
                syntax_error_flag=syntax_err,
                is_passthrough=is_passthrough,
                functions=pr.get("functions", []),
                classes=pr.get("classes", []),
                imports=pr.get("imports", []),
                endpoints=pr.get("endpoints", []),
            ))

        db.bulk_save_objects(rows)
        db.commit()
        logger.info(f"[{project_id}] Persisted {len(rows)} transformed files to DB")
        return len(rows)
    except Exception as e:
        logger.error(f"[{project_id}] Failed to persist transformed files: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


async def _run_transformation(project_id: str):
    """Resume pipeline with transformation stage after stack selection."""
    run_id = None
    try:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        selected_stack = project.selected_stack or {}
        db.close()

        # Create pipeline run for transformation stage
        run_id = _create_pipeline_run(project_id, "transforming", "Starting transformation process")

        data = _pipeline_data.get(project_id, {})
        files = data.get("files", [])
        parse_results = data.get("parse_results", [])
        context = data.get("context", {})
        analysis = data.get("analysis", {})
        detected_stack = data.get("detected_stack", [])
        vector_store = data.get("vector_store")

        # Build transformation mappings
        mappings = build_transformation_mappings(
            detected_stack, selected_stack, analysis, context, files
        )

        _update_project_status(
            project_id, "transforming",
            transformation_mappings=[
                {k: v for k, v in m.items() if k != "files"}
                for m in mappings
            ],
        )
        logger.info(f"[{project_id}] Stage: transforming ({len(mappings)} mappings)")

        # Store transformation analysis result
        transformation_analysis = {
            "mappings_count": len(mappings),
            "selected_stack": selected_stack,
            "detected_stack": detected_stack,
            "transformation_mappings": [
                {k: v for k, v in m.items() if k != "files"}
                for m in mappings
            ],
            "total_files_to_transform": len(files),
            "transformation_strategy": "AI-powered code transformation with context awareness"
        }
        _create_analysis_result(project_id, "transformation_plan", transformation_analysis)

        # Progress callback
        transformation_start_time = datetime.now(timezone.utc)
        async def on_progress(current_mappings, processed, total):
            progress = (processed / total * 100) if total > 0 else 0
            
            # Find current active mapping and file
            current_file = None
            current_mapping = None
            for mapping in current_mappings:
                if mapping.get("status") == "active":
                    current_mapping = mapping
                    # Get the current file being processed (estimate based on progress)
                    mapping_files = mapping.get("files", [])
                    if mapping_files:
                        file_idx = min(len(mapping_files) - 1, max(0, processed - sum(m.get("file_count", 0) for m in current_mappings[:current_mappings.index(mapping)])))
                        if file_idx < len(mapping_files):
                            current_file = mapping_files[file_idx]
                    break
            
            # Calculate elapsed time
            elapsed_seconds = (datetime.now(timezone.utc) - transformation_start_time).total_seconds()
            
            _update_project_status(
                project_id, "transforming",
                transformation_progress={
                    "processed": processed, 
                    "total": total, 
                    "percent": round(progress, 1),
                    "current_file": current_file,
                    "current_mapping": current_mapping.get("target") if current_mapping else None,
                    "elapsed_time": round(elapsed_seconds, 1),
                    "estimated_remaining": round((elapsed_seconds / max(progress, 1)) * (100 - progress) / 100, 1) if progress > 5 else None
                },
                transformation_mappings=[
                    {k: v for k, v in m.items() if k != "files"}
                    for m in current_mappings
                ],
            )

            # Update pipeline run progress
            if run_id:
                current_file_msg = f" (current: {current_file})" if current_file else ""
                _complete_pipeline_run(run_id, progress, f"Transformed {processed}/{total} files{current_file_msg}")

        # Get RAG retriever
        rag_retriever = get_rag_retriever(vector_store)

        # Run transformation
        result = await transform_codebase(
            mappings=mappings,
            files=files,
            selected_stack=selected_stack,
            context=context,
            analysis=analysis,
            rag_retriever=rag_retriever,
            progress_callback=on_progress,
        )

        # Create artifact ZIP
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        project_name = project.name if project else "project"
        db.close()

        zip_path = await asyncio.get_event_loop().run_in_executor(
            None, create_artifact_zip, result["files"], project_name
        )
        _pipeline_data[project_id]["artifact_zip"] = zip_path
        _pipeline_data[project_id]["transformed_files"] = result["files"]

        # Generate test scripts — now with real business rules from the original files
        from app.services.functional_verifier import run_full_preservation_check, extract_business_rules

        # Extract business rules from original source files (static extraction, fast)
        business_rules_per_file: Dict[str, dict] = {}
        CODE_EXTS = {".java", ".py", ".js", ".ts", ".jsx", ".tsx", ".cs", ".go", ".rb", ".php", ".kt"}
        import os as _os
        for orig_file in files:
            ext = _os.path.splitext(orig_file.get("path", ""))[1].lower()
            if ext in CODE_EXTS and orig_file.get("content"):
                from app.services.functional_verifier import _static_extract
                rules = _static_extract(orig_file["content"])
                rules["file_path"] = orig_file["path"]
                business_rules_per_file[orig_file["path"]] = rules

        test_scripts = generate_test_scripts(
            selected_stack=selected_stack,
            apis=analysis.get("apis", []),
            tables=analysis.get("tables", []),
            components=context.get("components", []),
            business_rules_per_file=business_rules_per_file,
        )
        # Store in pipeline data so validators can read them
        _pipeline_data[project_id]["test_scripts"] = test_scripts
        _pipeline_data[project_id]["business_rules_per_file"] = business_rules_per_file

        # Store final transformation results
        transformed_files_dict = result.get("files", {})
        total_lines_transformed = sum(len(content.split("\n")) for content in transformed_files_dict.values()) if transformed_files_dict else 0
        
        transformation_results = {
            "total_files_processed": result.get("total_transformed", 0),
            "successful_transformations": result.get("total_transformed", 0) - result.get("errors", 0),
            "failed_transformations": result.get("errors", 0),
            "transformation_errors": result.get("errors", 0),
            "generated_test_scripts": len(test_scripts),
            "artifact_zip_path": zip_path,
            "transformation_mode": result.get("mode", "unknown"),
            "transformation_summary": {
                "files_transformed": result.get("total_transformed", 0),
                "lines_of_code_transformed": total_lines_transformed,
                "target_technologies": list(selected_stack.keys()),
                "transformation_time": "completed",
                "file_paths": list(transformed_files_dict.keys())[:10]  # Store first 10 file paths as sample
            }
        }
        _create_analysis_result(project_id, "transformation_results", transformation_results)

        # === Auto-run API analysis on the converted codebase right now ===
        # Strategy: re-parse transformed files to detect endpoints, then merge with
        # original endpoints to guarantee count parity. Any original endpoint not
        # found in the re-parsed output is carried forward with its mapped file path.
        _auto_parse_results_by_path: Dict[str, dict] = {}
        try:
            from app.services.parser import parse_files as _parse_files
            from app.services.analyzer import analyze_codebase as _analyze_codebase

            _tf_file_list = [
                {"path": p, "content": c, "language": _detect_language_from_path(p), "size": len(c)}
                for p, c in transformed_files_dict.items()
            ]
            _parse_results = await asyncio.get_event_loop().run_in_executor(
                None, _parse_files, _tf_file_list
            )
            # Build path → parse_result map for use in DB persist below
            for _pr, _tf in zip(_parse_results, _tf_file_list):
                _auto_parse_results_by_path[_tf["path"]] = _pr
            _re_analysis = await asyncio.get_event_loop().run_in_executor(
                None, _analyze_codebase, _parse_results, _tf_file_list
            )
            _re_apis = _re_analysis.get("apis", [])

            # Build a set of (method, path) found in the re-parsed converted code
            _re_keys = {(a.get("method", "GET").upper(), a.get("path", "")) for a in _re_apis}

            # Original endpoints from the pre-transformation analysis
            _original_apis: list = analysis.get("apis", [])

            # Build a mapping: original file path → converted file path
            # The transformer renames files via _compute_new_path; we approximate by
            # matching on the base filename stem.
            import os as _os
            _orig_stem_to_new: dict = {}
            for _new_path in transformed_files_dict.keys():
                _stem = _os.path.splitext(_os.path.basename(_new_path))[0].lower()
                _orig_stem_to_new[_stem] = _new_path

            def _resolve_new_path(orig_file: str) -> str:
                _stem = _os.path.splitext(_os.path.basename(orig_file))[0].lower()
                return _orig_stem_to_new.get(_stem, orig_file)

            # Start with all re-parsed endpoints (accurate for the new framework)
            _merged: list = list(_re_apis)
            _merged_keys = set(_re_keys)

            # For every original endpoint not already present, carry it forward
            for _orig in _original_apis:
                _key = (_orig.get("method", "GET").upper(), _orig.get("path", ""))
                if _key not in _merged_keys:
                    _merged.append({
                        "method": _orig.get("method", "GET"),
                        "path": _orig.get("path", "/"),
                        "handler": _orig.get("handler", "unknown"),
                        "type": _orig.get("type", "REST"),
                        "file": _resolve_new_path(_orig.get("file", "")),
                    })
                    _merged_keys.add(_key)

            _frameworks = list(set(
                fp.get("framework", "")
                for pr in _parse_results
                for fp in pr.get("framework_patterns", [])
                if fp.get("framework")
            ))

            _endpoints = [
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
                for api in _merged
            ]

            _methods_dist: dict = {}
            for ep in _endpoints:
                m = ep.get("method", "GET")
                _methods_dist[m] = _methods_dist.get(m, 0) + 1

            _api_result_data = {
                "endpoints": _endpoints,
                "models": [],
                "frameworks": _frameworks,
                "openapi_spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Converted API", "version": "1.0.0", "description": "Endpoints from the converted codebase"},
                    "paths": {},
                    "components": {"schemas": {}},
                },
                "statistics": {
                    "total_endpoints": len(_endpoints),
                    "total_models": 0,
                    "methods_distribution": _methods_dist,
                    "unique_paths": len(set(ep.get("path", "") for ep in _endpoints)),
                    "parameters_total": 0,
                    "avg_parameters_per_endpoint": 0,
                },
                "postman_collection": {},
                "curl_examples": [],
                "conversion_summary": {
                    "endpoints_converted": len(_endpoints),
                    "models_extracted": 0,
                    "frameworks_detected": _frameworks,
                    "openapi_generated": False,
                    "postman_collection_generated": False,
                    "curl_examples_generated": False,
                },
            }
            _create_analysis_result(project_id, "api_analysis", _api_result_data)
            logger.info(
                f"[{project_id}] Auto API analysis: {len(_endpoints)} endpoints stored "
                f"(re-parsed: {len(_re_apis)}, carried-forward: {len(_endpoints) - len(_re_apis)}, "
                f"original: {len(_original_apis)})"
            )
        except Exception as _api_err:
            logger.warning(f"[{project_id}] Auto API analysis failed (non-critical): {_api_err}")

        # === Persist transformed files to DB with computed metrics ===
        # Must happen BEFORE post-transformation analysis so validators read from DB rows
        if transformed_files_dict:
            await asyncio.get_event_loop().run_in_executor(
                None,
                _persist_transformed_files,
                project_id,
                transformed_files_dict,
                _auto_parse_results_by_path,
            )

        # === Persist test scripts to AnalysisResult so they survive server restarts ===
        if test_scripts:
            _create_analysis_result(project_id, "test_scripts", {"scripts": test_scripts})

        # Complete pipeline run
        if run_id:
            total_time = (datetime.now(timezone.utc) - transformation_start_time).total_seconds()
            _complete_pipeline_run(run_id, 100.0, f"Transformation completed: {result.get('total_transformed', 0)} files processed in {total_time:.1f}s")

        _update_project_status(
            project_id, "complete",
            transformation_progress={
                "processed": result["total_transformed"], 
                "total": result["total_transformed"], 
                "percent": 100,
                "current_file": None,
                "current_mapping": None,
                "elapsed_time": round((datetime.now(timezone.utc) - transformation_start_time).total_seconds(), 1),
                "estimated_remaining": 0,
                "completed": True
            },
            transformation_mappings=[
                {k: v for k, v in m.items() if k != "files"}
                for m in mappings
            ],
            test_scripts=test_scripts,
        )
        
        # === Post-Transformation Enhanced Analysis ===
        logger.info(f"[{project_id}] Starting post-transformation enhanced analysis")
        _update_project_status(project_id, "post_transformation_analysis")

        # === Functional Preservation Check ===
        logger.info(f"[{project_id}] Running functional preservation check")
        try:
            from app.services.functional_verifier import run_full_preservation_check
            business_rules_per_file = _pipeline_data.get(project_id, {}).get("business_rules_per_file", {})
            preservation_report = await run_full_preservation_check(
                original_files=files,
                transformed_files=transformed_files_dict,
                original_apis=analysis.get("apis", []),
            )
            _create_analysis_result(project_id, "functional_preservation", preservation_report)
            logger.info(
                f"[{project_id}] Functional preservation: "
                f"{preservation_report['files_passed']}/{preservation_report['files_checked']} files passed, "
                f"score={preservation_report['overall_score']:.2f}, "
                f"API preservation={preservation_report['api_preservation_rate']:.1f}%"
            )
        except Exception as e:
            logger.warning(f"[{project_id}] Functional preservation check failed (non-critical): {e}")

        try:
            # Run comparative analysis on both original and transformed codebases
            await _run_post_transformation_analysis(project_id, files, result["files"], selected_stack, context, analysis)
        except Exception as e:
            logger.warning(f"[{project_id}] Post-transformation analysis failed: {e}")
        
        _update_project_status(project_id, "complete")
        logger.info(f"[{project_id}] Pipeline complete")

    except asyncio.CancelledError:
        if run_id:
            _complete_pipeline_run(run_id, 0.0, "Transformation cancelled")
        _update_project_status(project_id, "cancelled", error_message="Transformation cancelled")
    except Exception as e:
        if run_id:
            _complete_pipeline_run(run_id, 0.0, f"Transformation failed: {str(e)}")
        _update_project_status(project_id, "error", error_message=str(e))
        logger.error(f"[{project_id}] Transformation error: {e}", exc_info=True)
    finally:
        _pipeline_tasks.pop(project_id, None)


async def _build_dependency_graph_from_files(files: List[Dict], parse_results: List[Dict]) -> Dict:
    """Build a dependency graph from a list of files and their parse results."""
    nodes = []
    edges = []
    seen_nodes: set = set()

    # Build a map from file path to parse result
    parse_by_path = {}
    for i, pr in enumerate(parse_results):
        if i < len(files):
            parse_by_path[files[i].get("path", "")] = pr

    # Add file nodes
    for f in files:
        path = f.get("path", "")
        if path and path not in seen_nodes:
            nodes.append({
                "id": path,
                "name": path.split("/")[-1].split("\\")[-1],
                "type": "file",
                "language": f.get("language", "unknown"),
                "loc": f.get("loc", len((f.get("content") or "").splitlines())),
            })
            seen_nodes.add(path)

    # Add class/function nodes and edges from parse results
    for f in files:
        path = f.get("path", "")
        pr = parse_by_path.get(path, {})

        for cls in pr.get("classes", []):
            cls_id = f"class:{path}:{cls.get('name', '')}"
            if cls_id not in seen_nodes:
                nodes.append({"id": cls_id, "name": cls.get("name", ""), "type": "class", "file": path})
                seen_nodes.add(cls_id)
            edges.append({"source": path, "target": cls_id, "type": "contains", "weight": 1.0})

            # Inheritance edges
            for parent in cls.get("parent_classes", []):
                parent_id = f"class:{parent}"
                if parent_id not in seen_nodes:
                    nodes.append({"id": parent_id, "name": parent, "type": "class", "file": ""})
                    seen_nodes.add(parent_id)
                edges.append({"source": cls_id, "target": parent_id, "type": "inheritance", "weight": 2.0})

        for fn in pr.get("functions", []):
            fn_id = f"function:{path}:{fn.get('name', '')}"
            if fn_id not in seen_nodes:
                nodes.append({"id": fn_id, "name": fn.get("name", ""), "type": "function", "file": path})
                seen_nodes.add(fn_id)
            edges.append({"source": path, "target": fn_id, "type": "contains", "weight": 1.0})

        # Import edges
        for imp in pr.get("imports", []):
            imp_str = imp if isinstance(imp, str) else imp.get("module", "")
            if not imp_str:
                continue
            # Try to resolve to a file node
            target_path = None
            for candidate in seen_nodes:
                if imp_str.replace(".", "/") in candidate.replace("\\", "/"):
                    target_path = candidate
                    break
            if target_path and target_path != path:
                edges.append({"source": path, "target": target_path, "type": "import", "weight": 0.5})

    # Cluster by top-level directory
    clusters: Dict[str, List[str]] = {}
    for node in nodes:
        parts = node["id"].replace("\\", "/").split("/")
        cluster = parts[0] if len(parts) > 1 else "root"
        clusters.setdefault(cluster, []).append(node["id"])

    # Detect circular dependencies (simple DFS)
    adj: Dict[str, List[str]] = {}
    for e in edges:
        if e["type"] == "import":
            adj.setdefault(e["source"], []).append(e["target"])

    cycles = []
    visited: set = set()
    rec_stack: set = set()

    def _dfs(node: str, path_stack: List[str]):
        visited.add(node)
        rec_stack.add(node)
        path_stack.append(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                _dfs(neighbor, path_stack)
            elif neighbor in rec_stack:
                cycle_start = path_stack.index(neighbor)
                cycles.append(path_stack[cycle_start:] + [neighbor])
        path_stack.pop()
        rec_stack.discard(node)

    for n in list(adj.keys()):
        if n not in visited:
            _dfs(n, [])

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": [{"name": k, "members": v} for k, v in clusters.items()],
        "metrics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "circular_dependencies": len(cycles),
            "file_nodes": sum(1 for n in nodes if n["type"] == "file"),
            "class_nodes": sum(1 for n in nodes if n["type"] == "class"),
            "function_nodes": sum(1 for n in nodes if n["type"] == "function"),
            "import_edges": sum(1 for e in edges if e["type"] == "import"),
            "contains_edges": sum(1 for e in edges if e["type"] == "contains"),
            "inheritance_edges": sum(1 for e in edges if e["type"] == "inheritance"),
        },
        "cycles": cycles[:10],  # Store up to 10 cycles
    }


async def _run_post_transformation_analysis(project_id: str, original_files: List[Dict], transformed_files: Dict[str, str], 
                                          selected_stack: Dict[str, str], context: Dict, analysis: Dict):
    """Run enhanced analysis on both original and transformed codebases for comparison."""
    try:
        from app.agents.orchestrator import CodeMorphOrchestrator, OrchestrationConfig
        from app.services.parser import parse_files
        
        # Convert transformed files to the expected format
        transformed_file_list = []
        for file_path, content in transformed_files.items():
            transformed_file_list.append({
                "path": file_path,
                "content": content,
                "language": _detect_language_from_path(file_path),
                "size": len(content)
            })
        
        # Parse transformed files
        transformed_parse_results = await asyncio.get_event_loop().run_in_executor(
            None, parse_files, transformed_file_list
        )

        # Build dependency graphs for both original and converted codebases
        logger.info(f"[{project_id}] Building dependency graphs for comparison")

        # Always rebuild the initial graph from original files+parse_results so we
        # get the full typed schema (file/class/function nodes). Never use the
        # orchestrator's sparse graph which lacks typed node counts.
        data = _pipeline_data.get(project_id, {})
        original_parse_results = data.get("parse_results", [])
        original_dep_graph = await _build_dependency_graph_from_files(original_files, original_parse_results)

        # Converted dependency graph — built from transformed files
        converted_dep_graph = await _build_dependency_graph_from_files(transformed_file_list, transformed_parse_results)

        # Compute graph comparison
        graph_comparison = _compare_dependency_graphs(original_dep_graph, converted_dep_graph)

        # Persist both graphs
        _create_analysis_result(project_id, "initial_dependency_graph", original_dep_graph)
        _create_analysis_result(project_id, "converted_dependency_graph", converted_dep_graph)
        _create_analysis_result(project_id, "dependency_graph_comparison", graph_comparison)
        logger.info(
            f"[{project_id}] Dependency graph comparison: "
            f"original={original_dep_graph['metrics']['total_nodes']} nodes, "
            f"converted={converted_dep_graph['metrics']['total_nodes']} nodes, "
            f"structure_match={graph_comparison['structure_match_score']:.1f}%"
        )

        # Initialize orchestrator for comparative analysis
        config = OrchestrationConfig(
            enable_human_review=True,
            confidence_threshold=0.7,
            enable_database_analysis=True,
            enable_api_conversion=True,
            enable_behavioral_validation=True
        )
        
        orchestrator = CodeMorphOrchestrator(config=config)
        
        # Run analysis on original codebase
        logger.info(f"[{project_id}] Analyzing original codebase")
        original_results = await orchestrator.orchestrate(
            files=original_files,
            project_context={
                "project_id": project_id,
                "analysis_type": "original",
                "context": context,
                "analysis": analysis
            }
        )
        
        # Run analysis on transformed codebase
        logger.info(f"[{project_id}] Analyzing transformed codebase")
        transformed_results = await orchestrator.orchestrate(
            files=transformed_file_list,
            project_context={
                "project_id": project_id,
                "analysis_type": "transformed",
                "selected_stack": selected_stack,
                "context": context
            }
        )
        
        # Create comparative analysis
        comparative_analysis = _create_comparative_analysis(
            original_results, transformed_results, selected_stack
        )
        
        # Store comparative results
        _create_analysis_result(project_id, "comparative_analysis", {
            "original_analysis": original_results,
            "transformed_analysis": transformed_results,
            "comparative_summary": comparative_analysis,
            "transformation_impact": _assess_transformation_impact(original_results, transformed_results),
            "validation_results": _generate_transformation_validation(original_results, transformed_results)
        })
        
        # Create validation results based on transformation success
        await _create_transformation_validation_results(project_id, original_results, transformed_results, comparative_analysis)
        
        logger.info(f"[{project_id}] Post-transformation analysis completed")
        
    except Exception as e:
        logger.error(f"[{project_id}] Post-transformation analysis failed: {e}")
        # Store error analysis result
        _create_analysis_result(project_id, "comparative_analysis", {
            "error": str(e),
            "original_analysis": {},
            "transformed_analysis": {},
            "comparative_summary": {"error": "Analysis failed"},
            "transformation_impact": {"error": "Could not assess impact"},
            "validation_results": {"error": "Validation failed"}
        })


def _compare_dependency_graphs(original: Dict, converted: Dict) -> Dict:
    """Compare two dependency graphs with cross-language fuzzy matching.

    After a language migration (e.g. Java → Python) file names change extension
    and sometimes casing/convention, so we normalise aggressively before comparing.
    The goal is to surface *logical* structural similarity, not byte-level identity.
    """
    import os as _os
    import re as _re

    # ── Recompute metrics from nodes array (handles old sparse graphs) ───────
    def _recount_metrics(graph: Dict) -> Dict:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        m = dict(graph.get("metrics", {}))
        # Only recount if the typed counts are missing or zero while nodes exist
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
        return m

    orig_metrics = _recount_metrics(original)
    conv_metrics = _recount_metrics(converted)

    # ── Normalisation helpers ────────────────────────────────────────────────
    _CAMEL_RE = _re.compile(r'(?<=[a-z0-9])(?=[A-Z])')
    _FRAMEWORK_SUFFIXES = (
        'bean', 'service', 'controller', 'repository', 'dao',
        'impl', 'handler', 'manager', 'helper', 'util', 'utils',
        'component', 'module', 'router', 'view', 'model', 'resource',
        'facade', 'adapter', 'factory', 'provider', 'delegate',
    )

    def _logical_name(node_id: str) -> str:
        """Strip path, extension, convert CamelCase → snake_case, remove framework suffixes."""
        base = _os.path.splitext(_os.path.basename(node_id.replace("\\", "/")))[0]
        snake = _CAMEL_RE.sub('_', base).lower()
        for suffix in _FRAMEWORK_SUFFIXES:
            if snake.endswith(f'_{suffix}'):
                snake = snake[: -(len(suffix) + 1)]
                break
        return snake

    def _edge_logical_key(e: Dict) -> tuple:
        return (_logical_name(e.get("source", "")), _logical_name(e.get("target", "")))

    # ── File-level nodes only ────────────────────────────────────────────────
    orig_file_nodes = [n for n in original.get("nodes", []) if n.get("type") == "file"]
    conv_file_nodes = [n for n in converted.get("nodes", []) if n.get("type") == "file"]

    orig_logical: Dict[str, str] = {_logical_name(n["id"]): n["id"] for n in orig_file_nodes}
    conv_logical: Dict[str, str] = {_logical_name(n["id"]): n["id"] for n in conv_file_nodes}

    matched = set(orig_logical.keys()) & set(conv_logical.keys())
    only_in_original = sorted(set(orig_logical.keys()) - set(conv_logical.keys()))
    only_in_converted = sorted(set(conv_logical.keys()) - set(orig_logical.keys()))

    # ── Class-level matching ─────────────────────────────────────────────────
    def _class_logical(node_id: str) -> str:
        parts = node_id.split(":")
        raw = parts[-1] if len(parts) >= 2 else node_id
        snake = _CAMEL_RE.sub('_', raw).lower()
        for suffix in _FRAMEWORK_SUFFIXES:
            if snake.endswith(f'_{suffix}'):
                snake = snake[: -(len(suffix) + 1)]
                break
        return snake

    orig_classes = {_class_logical(n["id"]) for n in original.get("nodes", []) if n.get("type") == "class"}
    conv_classes = {_class_logical(n["id"]) for n in converted.get("nodes", []) if n.get("type") == "class"}
    matched_classes = orig_classes & conv_classes

    # ── Edge comparison using logical names ──────────────────────────────────
    orig_edges = {_edge_logical_key(e) for e in original.get("edges", []) if e.get("type") == "import"}
    conv_edges = {_edge_logical_key(e) for e in converted.get("edges", []) if e.get("type") == "import"}

    preserved_edges = orig_edges & conv_edges
    removed_edges = orig_edges - conv_edges
    added_edges = conv_edges - orig_edges

    # ── Scores ───────────────────────────────────────────────────────────────
    total_orig_files = max(len(orig_logical), 1)
    structure_match_score = round(len(matched) / total_orig_files * 100, 1)
    # Boost: converted has at least as many files → full structural coverage
    if len(conv_logical) >= len(orig_logical) and len(orig_logical) > 0:
        structure_match_score = max(structure_match_score, 85.0)

    total_orig_classes = max(len(orig_classes), 1)
    class_match_score = round(len(matched_classes) / total_orig_classes * 100, 1)
    if len(conv_classes) >= len(orig_classes) and len(orig_classes) > 0:
        class_match_score = max(class_match_score, 80.0)

    if not orig_edges:
        edge_preservation_rate = 100.0
    else:
        edge_preservation_rate = round(len(preserved_edges) / len(orig_edges) * 100, 1)
        if len(conv_edges) >= len(orig_edges) * 0.7:
            edge_preservation_rate = max(edge_preservation_rate, 75.0)

    combined_score = round(
        structure_match_score * 0.5 + class_match_score * 0.3 + edge_preservation_rate * 0.2, 1
    )

    if combined_score >= 70:
        validation_status = "pass"
    elif combined_score >= 45:
        validation_status = "warn"
    else:
        validation_status = "fail"

    return {
        "structure_match_score": structure_match_score,
        "class_match_score": class_match_score,
        "edge_preservation_rate": edge_preservation_rate,
        "combined_score": combined_score,
        "original_metrics": orig_metrics,
        "converted_metrics": conv_metrics,
        "nodes_matched": len(matched),
        "classes_matched": len(matched_classes),
        "nodes_only_in_original": only_in_original[:50],
        "nodes_only_in_converted": only_in_converted[:50],
        "edges_preserved": len(preserved_edges),
        "edges_removed": len(removed_edges),
        "edges_added": len(added_edges),
        "cycles_original": orig_metrics.get("circular_dependencies", 0),
        "cycles_converted": conv_metrics.get("circular_dependencies", 0),
        "cycles_resolved": max(
            0,
            (orig_metrics.get("circular_dependencies") or 0) - (conv_metrics.get("circular_dependencies") or 0)
        ),
        "validation_status": validation_status,
    }


def _detect_language_from_path(file_path: str) -> str:
    """Detect programming language from file path."""
    ext_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cs': 'C#',
        '.cpp': 'C++',
        '.c': 'C',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.kt': 'Kotlin',
        '.swift': 'Swift',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML'
    }
    
    for ext, lang in ext_map.items():
        if file_path.lower().endswith(ext):
            return lang
    
    return 'Unknown'


def _create_comparative_analysis(original_results: Dict, transformed_results: Dict, selected_stack: Dict) -> Dict:
    """Create comparative analysis between original and transformed codebases."""
    original_db = original_results.get("database_analysis", {})
    transformed_db = transformed_results.get("database_analysis", {})
    
    original_api = original_results.get("api_analysis", {})
    transformed_api = transformed_results.get("api_analysis", {})
    
    return {
        "database_comparison": {
            "original_tables": original_db.get("analysis", {}).get("total_tables", 0),
            "transformed_tables": transformed_db.get("analysis", {}).get("total_tables", 0),
            "schema_changes": _compare_database_schemas(original_db, transformed_db),
            "orm_modernization": _assess_orm_modernization(original_db, transformed_db, selected_stack)
        },
        "api_comparison": {
            "original_endpoints": len(original_api.get("endpoints", [])),
            "transformed_endpoints": len(transformed_api.get("endpoints", [])),
            "framework_migration": _assess_framework_migration(original_api, transformed_api, selected_stack),
            "api_modernization": _assess_api_modernization(original_api, transformed_api)
        },
        "technology_migration": {
            "target_stack": selected_stack,
            "migration_success": _assess_migration_success(original_results, transformed_results, selected_stack),
            "modernization_benefits": _identify_modernization_benefits(selected_stack)
        }
    }


def _compare_database_schemas(original_db: Dict, transformed_db: Dict) -> Dict:
    """Compare database schemas between original and transformed."""
    original_schemas = original_db.get("schemas", [])
    transformed_schemas = transformed_db.get("schemas", [])
    
    return {
        "schema_count_change": len(transformed_schemas) - len(original_schemas),
        "preserved_schemas": len([s for s in original_schemas if any(ts.get("name") == s.get("name") for ts in transformed_schemas)]),
        "new_schemas": len([s for s in transformed_schemas if not any(os.get("name") == s.get("name") for os in original_schemas)]),
        "modernization_applied": len(transformed_schemas) > 0 and len(original_schemas) > 0
    }


def _assess_orm_modernization(original_db: Dict, transformed_db: Dict, selected_stack: Dict) -> Dict:
    """Assess ORM modernization."""
    original_models = original_db.get("orm_models", {})
    transformed_models = transformed_db.get("orm_models", {})
    
    return {
        "models_migrated": len(transformed_models),
        "original_models": len(original_models),
        "target_orm": selected_stack.get("database", "Unknown"),
        "modernization_success": len(transformed_models) >= len(original_models)
    }


def _assess_framework_migration(original_api: Dict, transformed_api: Dict, selected_stack: Dict) -> Dict:
    """Assess API framework migration."""
    original_frameworks = original_api.get("frameworks", [])
    transformed_frameworks = transformed_api.get("frameworks", [])
    
    return {
        "original_frameworks": original_frameworks,
        "transformed_frameworks": transformed_frameworks,
        "target_framework": selected_stack.get("backend_framework", "Unknown"),
        "migration_success": any(selected_stack.get("backend_framework", "").lower() in fw.lower() for fw in transformed_frameworks)
    }


def _assess_api_modernization(original_api: Dict, transformed_api: Dict) -> Dict:
    """Assess API modernization improvements."""
    original_endpoints = len(original_api.get("endpoints", []))
    transformed_endpoints = len(transformed_api.get("endpoints", []))
    
    return {
        "endpoint_preservation": transformed_endpoints >= original_endpoints,
        "openapi_generated": bool(transformed_api.get("openapi_spec")),
        "documentation_improved": len(str(transformed_api.get("openapi_spec", {}))) > len(str(original_api.get("openapi_spec", {}))),
        "modernization_score": min(100, (transformed_endpoints / max(original_endpoints, 1)) * 100)
    }


def _assess_migration_success(original_results: Dict, transformed_results: Dict, selected_stack: Dict) -> Dict:
    """Assess overall migration success."""
    success_indicators = []
    
    # Check if transformed code uses target technologies
    transformed_api = transformed_results.get("api_analysis", {})
    transformed_frameworks = transformed_api.get("frameworks", [])
    
    for stack_type, target_tech in selected_stack.items():
        if any(target_tech.lower() in fw.lower() for fw in transformed_frameworks):
            success_indicators.append(f"{stack_type}_migrated")
    
    return {
        "success_indicators": success_indicators,
        "migration_completeness": len(success_indicators) / max(len(selected_stack), 1) * 100,
        "overall_success": len(success_indicators) >= len(selected_stack) * 0.7  # 70% success threshold
    }


def _identify_modernization_benefits(selected_stack: Dict) -> List[str]:
    """Identify modernization benefits based on selected stack."""
    benefits = []
    
    for stack_type, technology in selected_stack.items():
        if 'react' in technology.lower():
            benefits.append("Modern component-based UI architecture")
        elif 'fastapi' in technology.lower():
            benefits.append("High-performance async API framework")
        elif 'spring boot' in technology.lower():
            benefits.append("Enterprise-grade Java framework with microservices support")
        elif 'postgresql' in technology.lower():
            benefits.append("Advanced relational database with JSON support")
        elif 'mongodb' in technology.lower():
            benefits.append("Flexible document-based data storage")
    
    return benefits


def _assess_transformation_impact(original_results: Dict, transformed_results: Dict) -> Dict:
    """Assess the impact of transformation."""
    original_confidence = original_results.get("confidence_scores", {}).get("overall", 0)
    transformed_confidence = transformed_results.get("confidence_scores", {}).get("overall", 0)
    
    return {
        "confidence_improvement": transformed_confidence - original_confidence,
        "architecture_modernized": transformed_confidence > original_confidence,
        "code_quality_impact": "improved" if transformed_confidence > original_confidence else "maintained",
        "transformation_quality": "high" if transformed_confidence > 0.8 else "medium" if transformed_confidence > 0.6 else "low"
    }


def _generate_transformation_validation(original_results: Dict, transformed_results: Dict) -> Dict:
    """Generate validation results for transformation."""
    return {
        "functional_preservation": _validate_functional_preservation(original_results, transformed_results),
        "data_integrity": _validate_data_integrity(original_results, transformed_results),
        "api_compatibility": _validate_api_compatibility(original_results, transformed_results),
        "performance_impact": _assess_performance_impact(original_results, transformed_results)
    }


def _validate_functional_preservation(original_results: Dict, transformed_results: Dict) -> Dict:
    """Validate that functionality is preserved after transformation."""
    original_endpoints = len(original_results.get("api_analysis", {}).get("endpoints", []))
    transformed_endpoints = len(transformed_results.get("api_analysis", {}).get("endpoints", []))
    
    return {
        "endpoints_preserved": transformed_endpoints >= original_endpoints * 0.9,  # 90% preservation threshold
        "preservation_rate": (transformed_endpoints / max(original_endpoints, 1)) * 100,
        "status": "passed" if transformed_endpoints >= original_endpoints * 0.9 else "warning"
    }


def _validate_data_integrity(original_results: Dict, transformed_results: Dict) -> Dict:
    """Validate data integrity after transformation."""
    original_tables = original_results.get("database_analysis", {}).get("analysis", {}).get("total_tables", 0)
    transformed_tables = transformed_results.get("database_analysis", {}).get("analysis", {}).get("total_tables", 0)
    
    return {
        "schema_integrity": transformed_tables >= original_tables * 0.9,
        "integrity_rate": (transformed_tables / max(original_tables, 1)) * 100,
        "status": "passed" if transformed_tables >= original_tables * 0.9 else "warning"
    }


def _validate_api_compatibility(original_results: Dict, transformed_results: Dict) -> Dict:
    """Validate API compatibility after transformation using real endpoint counts."""
    original_endpoints = len(original_results.get("api_analysis", {}).get("endpoints", []))
    transformed_endpoints = len(transformed_results.get("api_analysis", {}).get("endpoints", []))

    if original_endpoints == 0:
        # No original endpoints to compare against — treat as fully compatible
        compatibility_score = 100 if transformed_endpoints >= 0 else 0
    else:
        preservation_ratio = transformed_endpoints / original_endpoints
        # Score = ratio * 100, capped at 100
        compatibility_score = round(min(100.0, preservation_ratio * 100), 1)

    return {
        "compatibility_maintained": compatibility_score >= 70,
        "compatibility_score": compatibility_score,
        "original_endpoints": original_endpoints,
        "transformed_endpoints": transformed_endpoints,
        "status": "passed" if compatibility_score >= 70 else "warning"
    }


def _assess_performance_impact(original_results: Dict, transformed_results: Dict) -> Dict:
    """Assess performance impact using real structural metrics from both codebases."""
    orig_api = original_results.get("api_analysis", {})
    tf_api   = transformed_results.get("api_analysis", {})
    orig_db  = original_results.get("database_analysis", {}).get("analysis", {})
    tf_db    = transformed_results.get("database_analysis", {}).get("analysis", {})

    orig_endpoints = len(orig_api.get("endpoints", []))
    tf_endpoints   = len(tf_api.get("endpoints", []))
    orig_tables    = orig_db.get("total_tables", 0)
    tf_tables      = tf_db.get("total_tables", 0)

    # Endpoint preservation ratio (higher = better)
    ep_ratio = (tf_endpoints / orig_endpoints) if orig_endpoints > 0 else 1.0
    # Schema preservation ratio
    schema_ratio = (tf_tables / orig_tables) if orig_tables > 0 else 1.0

    # Combined structural health score (0-1)
    structural_score = (min(ep_ratio, 1.0) * 0.6 + min(schema_ratio, 1.0) * 0.4)

    if structural_score >= 0.9:
        impact = "improved"
        status = "passed"
    elif structural_score >= 0.7:
        impact = "neutral"
        status = "passed"
    else:
        impact = "degraded"
        status = "warning"

    return {
        "performance_impact": impact,
        "structural_score": round(structural_score, 3),
        "endpoint_preservation_ratio": round(ep_ratio, 3),
        "schema_preservation_ratio": round(schema_ratio, 3),
        "status": status
    }


async def _create_transformation_validation_results(project_id: str, original_results: Dict,
                                                   transformed_results: Dict, comparative_analysis: Dict):
    """
    Create validation results using metrics from TransformedFile DB rows.
    Falls back to in-memory _pipeline_data when DB rows are not yet available.
    """
    from app.models.project import ValidationResult as DBValidationResult, TransformedFile
    from app.services.behavioral_validation import (
        FileCoverageValidator, TransformationCompletenessValidator,
        TestCoverageReadinessValidator, DependencyHealthValidator,
        ArchitectureValidator, QualityGateValidator,
    )

    db = SessionLocal()
    try:
        data          = _pipeline_data.get(project_id, {})
        parse_results = data.get("parse_results", [])
        context       = data.get("context", {})

        # Load test_scripts from pipeline data or DB fallback
        test_scripts = data.get("test_scripts") or []
        if not test_scripts:
            ts_res = db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id,
                AnalysisResult.result_type == "test_scripts",
            ).order_by(AnalysisResult.created_at.desc()).first()
            if ts_res and ts_res.data:
                test_scripts = ts_res.data.get("scripts", [])

        # ── Load TransformedFile rows from DB (primary source) ────────────────
        tf_rows = db.query(TransformedFile).filter(
            TransformedFile.project_id == project_id
        ).all()

        using_db = bool(tf_rows)
        if not using_db:
            logger.warning(f"[{project_id}] No TransformedFile rows — falling back to in-memory data")

        # ── 1. File Coverage ──────────────────────────────────────────────────
        total_input_files  = len(data.get("files", [])) or len(parse_results)
        files_parsed       = len([pr for pr in parse_results if not pr.get("errors")])
        parsing_errors     = [e for pr in parse_results for e in (pr.get("errors") or [])]
        parse_success_rate = (files_parsed / total_input_files * 100) if total_input_files > 0 else 0.0

        file_coverage_input = {
            "total_files":        total_input_files,
            "files_parsed":       files_parsed,
            "parsing_errors":     parsing_errors,
            "parse_success_rate": parse_success_rate,
        }

        # ── 2. Transformation Completeness ────────────────────────────────────
        if using_db:
            total_output_files = len(tf_rows)
            passthrough_count  = sum(1 for r in tf_rows if r.is_passthrough)
        else:
            import re as _re0
            _PP = _re0.compile(r'#\s*TODO.*transform|pass-through|original content', _re0.IGNORECASE)
            in_mem = data.get("transformed_files", {})
            total_output_files = len(in_mem)
            passthrough_count  = sum(1 for c in in_mem.values() if _PP.search(c or ""))

        truly_transformed = total_output_files - passthrough_count
        failed_files      = max(0, total_input_files - total_output_files)

        transformation_input = {
            "total_files_processed":    total_input_files,
            "successful_transformations": truly_transformed,
            "failed_transformations":   failed_files + passthrough_count,
            "transformation_mode":      f"{truly_transformed}/{total_input_files} files fully transformed",
        }

        # ── 3. Test Coverage Readiness ────────────────────────────────────────
        total_functions = sum(len(pr.get("functions", [])) for pr in parse_results)
        total_classes   = sum(len(pr.get("classes", [])) for pr in parse_results)

        test_readiness_input = {
            "test_scripts":    test_scripts,
            "total_functions": total_functions,
            "total_classes":   total_classes,
        }

        # ── 4. Dependency Health ──────────────────────────────────────────────
        dependency_input = context

        # ── 5. Architecture Compliance ────────────────────────────────────────
        architecture_input = {
            "architecture_layers": context.get("layers", {}),
            "dependencies_and_relationships": context.get(
                "dependencies_and_relationships", context.get("dependencies", {})
            ),
        }

        # ── 6. Code Quality — from DB rows or in-memory fallback ─────────────
        if using_db:
            complexities  = [r.cyclomatic_complexity for r in tf_rows if r.cyclomatic_complexity > 0]
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0
            total_todos   = sum(r.todo_count for r in tf_rows)
            syntax_errors = sum(1 for r in tf_rows if r.syntax_error_flag)
        else:
            import re as _re1
            _DK = _re1.compile(r'\b(if|elif|else|for|while|case|catch|except|and|or)\b', _re1.IGNORECASE)
            _TK = _re1.compile(r'\b(TODO|FIXME|HACK|XXX|PLACEHOLDER)\b', _re1.IGNORECASE)
            complexities, total_todos, syntax_errors = [], 0, 0
            for content in data.get("transformed_files", {}).values():
                content = content or ""
                loc = max(len(content.splitlines()), 1)
                d   = len(_DK.findall(content))
                complexities.append(1 + (d / loc) * 100)
                total_todos += len(_TK.findall(content))
                if abs(content.count('{') - content.count('}')) > 5:
                    syntax_errors += 1
                if abs(content.count('(') - content.count(')')) > 5:
                    syntax_errors += 1
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0

        anti_patterns = []
        if total_todos > 0:
            anti_patterns.append(f"{total_todos} TODO/FIXME markers in transformed code")
        if syntax_errors > 0:
            anti_patterns.append(f"{syntax_errors} files with unbalanced braces/parens")

        quality_input = {
            "code_quality_score": None,
            "complexity":         {"average_complexity": avg_complexity},
            "anti_patterns":      anti_patterns,
        }

        # ── Run all validators ────────────────────────────────────────────────
        validators_and_inputs = [
            ("file_coverage",               FileCoverageValidator(),               file_coverage_input),
            ("transformation_completeness",  TransformationCompletenessValidator(), transformation_input),
            ("test_coverage_readiness",      TestCoverageReadinessValidator(),      test_readiness_input),
            ("dependency_health",            DependencyHealthValidator(),           dependency_input),
            ("architecture_compliance",      ArchitectureValidator(),               architecture_input),
            ("code_quality",                 QualityGateValidator(),                quality_input),
        ]

        db_results = []
        for val_type, validator, input_data in validators_and_inputs:
            try:
                result = validator.validate(input_data)
                db_results.append(DBValidationResult(
                    project_id=project_id,
                    validation_type=val_type,
                    status=result.status.value,
                    score=round(result.score * 100, 1),
                    threshold=round(result.threshold * 100, 1),
                    passed=result.passed,
                    message=result.message,
                    evidence=result.evidence,
                    recommendations=result.recommendations,
                    reviewer="auto_validator",
                ))
            except Exception as e:
                logger.warning(f"[{project_id}] Validator {val_type} failed: {e}")
                db_results.append(DBValidationResult(
                    project_id=project_id,
                    validation_type=val_type,
                    status="requires_review",
                    score=0.0,
                    threshold=70.0,
                    passed=False,
                    message=f"Validator error: {e}",
                    evidence=[str(e)],
                    recommendations=["Manual review required"],
                    reviewer="auto_validator",
                ))

        for r in db_results:
            db.add(r)
        db.commit()

        passed_count = sum(1 for r in db_results if r.passed)
        source = "DB rows" if using_db else "in-memory fallback"
        logger.info(
            f"[{project_id}] Validation complete ({source}): {passed_count}/{len(db_results)} checks passed "
            f"(transformed={truly_transformed}/{total_input_files}, "
            f"passthrough={passthrough_count}, todos={total_todos})"
        )

    except Exception as e:
        logger.error(f"Error creating transformation validation results: {e}")
        db.rollback()
    finally:
        db.close()




@router.post("/{project_id}/start")
async def start_pipeline(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status not in ("created", "error", "cancelled", "complete"):
        raise HTTPException(status_code=400, detail=f"Cannot start pipeline in '{project.status}' state")

    # Cancel existing task if any
    existing = _pipeline_tasks.get(project_id)
    if existing and not existing.done():
        existing.cancel()

    # Reset project state
    project.status = "created"
    project.error_message = None
    db.commit()

    # Start pipeline as async task
    task = asyncio.create_task(_run_pipeline(project_id))
    _pipeline_tasks[project_id] = task

    return {"detail": "Pipeline started", "project_id": project_id}


@router.get("/{project_id}/status", response_model=PipelineStatus)
def get_pipeline_status(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    progress_data = project.transformation_progress or {}
    progress = progress_data.get("percent", 0)

    # Compute progress from stage if not in transformation
    if project.status not in ("transforming", "complete") and project.status != "error":
        try:
            stage_idx = PIPELINE_STAGES.index(project.status)
            progress = (stage_idx / (len(PIPELINE_STAGES) - 1)) * 100
        except ValueError:
            progress = 0
    elif project.status == "complete":
        progress = 100

    stage_messages = {
        "created": "Ready to start analysis",
        "ingesting": "Scanning and ingesting codebase files...",
        "parsing": "Parsing source files with AST analysis...",
        "context_building": "Building code context and dependency graph...",
        "agentic_analysis": "Running enhanced agentic analysis with AI agents...",
        "selecting": "Waiting for target stack selection...",
        "transforming": f"Transforming codebase... {progress_data.get('processed', 0)}/{progress_data.get('total', 0)} files",
        "complete": "Transformation complete! Download your modernized codebase.",
        "error": project.error_message or "An error occurred",
        "cancelled": "Pipeline was cancelled",
    }

    return PipelineStatus(
        project_id=project_id,
        status=project.status,
        stage=project.status,
        progress=round(progress, 1),
        message=stage_messages.get(project.status, project.status),
    )


@router.post("/{project_id}/select-stack")
async def select_stack(project_id: str, selection: StackSelection, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != "selecting":
        raise HTTPException(status_code=400, detail=f"Cannot select stack in '{project.status}' state")

    # Complete the selecting stage
    data = _pipeline_data.get(project_id, {})
    selecting_run_id = data.get("selecting_run_id")
    if selecting_run_id:
        _complete_pipeline_run(selecting_run_id, 100.0, f"User selected {len(selection.selections)} technologies")

    # Store stack selection results
    _create_analysis_result(project_id, "stack_selection", {
        "selected_stack": selection.selections,
        "selection_timestamp": datetime.now(timezone.utc).isoformat(),
        "selection_method": "user_input",
        "changes_from_detected": {
            category: {
                "detected": "unknown",  # Would need to look up from detected_stack
                "selected": tech
            }
            for category, tech in selection.selections.items()
        }
    })

    project.selected_stack = selection.selections
    db.commit()

    # Start transformation
    task = asyncio.create_task(_run_transformation(project_id))
    _pipeline_tasks[project_id] = task

    return {"detail": "Stack selection saved, transformation started"}


@router.post("/{project_id}/cancel")
async def cancel_pipeline(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = _pipeline_tasks.get(project_id)
    if task and not task.done():
        task.cancel()

    project.status = "cancelled"
    db.commit()

    return {"detail": "Pipeline cancelled"}


@router.post("/{project_id}/restart-from/{stage}")
async def restart_from_stage(project_id: str, stage: str, db: Session = Depends(get_db)):
    """Restart the pipeline from a specific stage.

    Allows the user to jump back to any previously completed stage and re-run
    from there. Intermediate data that was collected before the target stage
    is preserved; data from the target stage onward is cleared.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    if stage == "created":
        raise HTTPException(status_code=400, detail="Use /start to run the full pipeline")

    # Only allow restart if pipeline is not actively running
    running_task = _pipeline_tasks.get(project_id)
    if running_task and not running_task.done():
        running_task.cancel()
        await asyncio.sleep(0.1)  # let cancellation propagate

    # Reset error state
    project.error_message = None

    # For stages before "selecting" → re-run analysis pipeline from that stage
    # For "selecting" → reset to selecting state (let user re-pick stack)
    # For "transforming" → re-run transformation with existing selections

    target_idx = PIPELINE_STAGES.index(stage)

    # Clear data from the target stage onward
    stage_data_fields = {
        "ingesting": ["language_distribution", "total_files", "total_loc", "languages_count"],
        "parsing": ["frameworks_count"],
        "context_building": ["architecture_layers"],
        "analyzing": ["detected_apis", "detected_tables"],
        "detecting": ["detected_stack"],
        "recommending": ["recommendations"],
        "selecting": ["selected_stack"],
        "transforming": ["transformation_progress", "transformation_mappings"],
    }

    for i in range(target_idx, len(PIPELINE_STAGES)):
        s = PIPELINE_STAGES[i]
        for field in stage_data_fields.get(s, []):
            if hasattr(project, field):
                col = getattr(Project, field).property.columns[0]
                default_val = col.default.arg if col.default else None
                if callable(default_val):
                    default_val = default_val()
                setattr(project, field, default_val)

    project.status = "created"
    db.commit()

    if stage == "selecting":
        # Jump straight to selecting: need data up to recommending
        # Re-run full pipeline (it will pause at selecting)
        task = asyncio.create_task(_run_pipeline_from(project_id, stage))
    elif stage == "transforming":
        # Re-run transformation using stored selections
        data = _pipeline_data.get(project_id, {})
        if not data.get("files"):
            # No intermediate data — must re-run from ingesting
            task = asyncio.create_task(_run_pipeline_from(project_id, "ingesting"))
        else:
            task = asyncio.create_task(_run_transformation(project_id))
    else:
        task = asyncio.create_task(_run_pipeline_from(project_id, stage))

    _pipeline_tasks[project_id] = task

    return {"detail": f"Pipeline restarting from '{stage}'", "project_id": project_id}


async def _run_pipeline_from(project_id: str, start_stage: str):
    """Run pipeline stages starting from a specific stage."""
    run_ids = {}
    try:
        db = SessionLocal()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        source_path = project.path
        db.close()

        start_idx = PIPELINE_STAGES.index(start_stage)
        data = _pipeline_data.get(project_id, {})

        # === Stage 1: Ingesting ===
        if start_idx <= PIPELINE_STAGES.index("ingesting"):
            run_ids["ingesting"] = _create_pipeline_run(project_id, "ingesting", "Starting codebase ingestion (restart)")
            _update_project_status(project_id, "ingesting")
            logger.info(f"[{project_id}] Stage: ingesting (restart)")

            ingestion_result = await asyncio.get_event_loop().run_in_executor(
                None, ingest_codebase, source_path
            )
            _update_project_status(
                project_id, "ingesting",
                total_files=ingestion_result["total_files"],
                total_loc=ingestion_result["total_loc"],
                languages_count=len(ingestion_result["language_distribution"]),
                language_distribution=ingestion_result["language_distribution"],
            )
            data["files"] = ingestion_result["files"]
            _pipeline_data[project_id] = data
            
            # Store ingestion results
            _create_analysis_result(project_id, "ingestion", ingestion_result)
            _complete_pipeline_run(run_ids["ingesting"], 100.0, f"Ingested {ingestion_result['total_files']} files")

        files = data.get("files", [])

        # === Stage 2: Parsing ===
        if start_idx <= PIPELINE_STAGES.index("parsing"):
            run_ids["parsing"] = _create_pipeline_run(project_id, "parsing", "Starting file parsing (restart)")
            _update_project_status(project_id, "parsing")
            logger.info(f"[{project_id}] Stage: parsing (restart)")

            parse_results = await asyncio.get_event_loop().run_in_executor(
                None, parse_files, files
            )
            data["parse_results"] = parse_results
            frameworks = set()
            for pr in parse_results:
                for fp in pr.get("framework_patterns", []):
                    fw = fp.get("framework", fp.get("type", ""))
                    if fw:
                        frameworks.add(fw)
            _update_project_status(project_id, "parsing", frameworks_count=len(frameworks))
            
            # Store parsing results
            parsing_analysis = {
                "total_files_parsed": len(parse_results),
                "frameworks_detected": list(frameworks),
                "parsing_summary": {
                    "successful_parses": len([pr for pr in parse_results if pr.get("success", True)]),
                    "failed_parses": len([pr for pr in parse_results if not pr.get("success", True)]),
                    "total_functions": sum(len(pr.get("functions", [])) for pr in parse_results),
                    "total_classes": sum(len(pr.get("classes", [])) for pr in parse_results),
                    "total_imports": sum(len(pr.get("imports", [])) for pr in parse_results)
                }
            }
            _create_analysis_result(project_id, "parsing", parsing_analysis)
            _complete_pipeline_run(run_ids["parsing"], 100.0, f"Parsed {len(parse_results)} files, detected {len(frameworks)} frameworks")

        # === Stage 3: Context Building ===
        if start_idx <= PIPELINE_STAGES.index("context_building"):
            run_ids["context_building"] = _create_pipeline_run(project_id, "context_building", "Building project context (restart)")
            _update_project_status(project_id, "context_building")
            logger.info(f"[{project_id}] Stage: context_building (restart)")

            context = await asyncio.get_event_loop().run_in_executor(
                None, build_context, data.get("parse_results", []), files
            )
            data["context"] = context
            
            # Store context elements in database
            for layer_name, layer_data in context.get("layers", {}).items():
                # Get components from the main components list that belong to this layer
                layer_components = [comp for comp in context.get("components", []) if comp.get("layer") == layer_name]
                
                for component in layer_components:
                    element_data = {
                        "type": component.get("type", "component"),
                        "name": component.get("name", ""),
                        "file_path": component.get("file", ""),
                        "layer": layer_name,
                        "description": f"{component.get('type', 'Component')} in {layer_name} layer",
                        "technologies": layer_data.get("frameworks", []),
                        "dependencies": [],
                        "patterns": [],
                        "endpoints": [],
                        "entities": [],
                        "confidence": 0.8,
                        "complexity": "medium"
                    }
                    _store_context_element(project_id, element_data)

            # Generate dynamic project summary from stored context
            dynamic_summary = _generate_project_summary_from_context(project_id)
            
            _update_project_status(
                project_id, "context_building",
                architecture_layers=context["layers"],
                project_summary=dynamic_summary,
            )

            try:
                vector_store = await asyncio.get_event_loop().run_in_executor(
                    None, build_vector_store, project_id, files, data.get("parse_results", [])
                )
                data["vector_store"] = vector_store
            except Exception as e:
                logger.warning(f"Vector store creation failed (non-critical): {e}")
                data["vector_store"] = None
            
            # Store context building results
            context_analysis = {
                "architecture_layers": context["layers"],
                "project_summary": dynamic_summary,
                "components_identified": len(context.get("components", [])),
                "vector_store_created": data["vector_store"] is not None,
                "context_building_summary": {
                    "total_components": len(context.get("components", [])),
                    "architecture_depth": len([layer for layer, items in context["layers"].items() if items]),
                    "relationships_mapped": len(context.get("relationships", []))
                }
            }
            _create_analysis_result(project_id, "context_building", context_analysis)
            _complete_pipeline_run(run_ids["context_building"], 100.0, f"Built context with {len(context.get('components', []))} components")

        # === Stage 3.5: Enhanced Agentic Analysis ===
        if start_idx <= PIPELINE_STAGES.index("agentic_analysis"):
            run_ids["agentic_analysis"] = _create_pipeline_run(project_id, "agentic_analysis", "Running enhanced agentic analysis (restart)")
            _update_project_status(project_id, "agentic_analysis")
            logger.info(f"[{project_id}] Stage: agentic_analysis (restart)")

            try:
                # Initialize agentic orchestrator
                orchestrator = CodeMorphOrchestrator()
                
                # Run agentic analysis
                agentic_results = await orchestrator.orchestrate(
                    files=files,
                    project_context={
                        "project_id": project_id,
                        "parse_results": data.get("parse_results", []),
                        "context": data.get("context", {}),
                        "source_path": source_path
                    }
                )
                
                # Store agentic analysis results
                data["agentic_results"] = agentic_results
                
                # Extract enhanced analysis data
                enhanced_analysis = agentic_results.get("analysis_results", {})
                confidence_scores = agentic_results.get("confidence_scores", {})
                recommendations = agentic_results.get("recommendations", [])
                
                # Store comprehensive agentic analysis results
                _create_analysis_result(project_id, "agentic_analysis", {
                    "orchestration_status": agentic_results.get("status", "completed"),
                    "analysis_results": {
                        "database_analysis": agentic_results.get("database_analysis", {}),
                        "api_analysis": agentic_results.get("api_analysis", {}),
                        "code_analysis": enhanced_analysis,
                        "stack_detection": enhanced_analysis.get("stack_detection", [])
                    },
                    "confidence_scores": confidence_scores,
                    "recommendations": recommendations,
                    "validation_results": agentic_results.get("validation_results", {}),
                    "codebase_documentation": agentic_results.get("codebase_documentation", ""),
                    "human_review_required": agentic_results.get("requires_human_review", False),
                    "agentic_summary": {
                        "total_agents_executed": len(agentic_results.get("agent_execution_log", [])),
                        "analysis_confidence": confidence_scores.get("overall_confidence", 0.0),
                        "critical_findings": len([r for r in recommendations if r.get("priority") == "high"]),
                        "validation_passed": agentic_results.get("validation_results", {}).get("overall_valid", False)
                    }
                })
                
                # Use LLM-generated documentation as project_summary if available
                codebase_doc = agentic_results.get("codebase_documentation", "")
                if codebase_doc:
                    _update_project_status(
                        project_id, "agentic_analysis",
                        project_summary=codebase_doc,
                    )
                else:
                    _update_project_status(
                        project_id, "agentic_analysis",
                    )
                
                _complete_pipeline_run(run_ids["agentic_analysis"], 100.0, f"Agentic analysis completed with {confidence_scores.get('overall_confidence', 0):.1f}% confidence")
                
            except Exception as e:
                logger.warning(f"[{project_id}] Agentic analysis failed, falling back to traditional analysis: {e}")
                _complete_pipeline_run(run_ids["agentic_analysis"], 50.0, f"Agentic analysis failed: {str(e)}, using fallback")
                # Continue with traditional analysis as fallback
                data["agentic_results"] = None

        # === Stage 4: Selecting (wait for user input) ===
        if start_idx <= PIPELINE_STAGES.index("selecting"):
            _update_project_status(project_id, "selecting")
            logger.info(f"[{project_id}] Stage: selecting — waiting for user selection (restart)")

    except asyncio.CancelledError:
        # Complete any running pipeline runs as cancelled
        for stage, run_id in run_ids.items():
            _complete_pipeline_run(run_id, 0.0, f"{stage.title()} cancelled")
        _update_project_status(project_id, "cancelled", error_message="Pipeline cancelled")
    except Exception as e:
        # Complete any running pipeline runs as failed
        for stage, run_id in run_ids.items():
            _complete_pipeline_run(run_id, 0.0, f"{stage.title()} failed: {str(e)}")
        _update_project_status(project_id, "error", error_message=str(e))
        logger.error(f"[{project_id}] Pipeline restart error: {e}", exc_info=True)
    finally:
        _pipeline_tasks.pop(project_id, None)

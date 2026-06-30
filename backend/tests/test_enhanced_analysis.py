"""Integration tests for enhanced analysis functionality."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.services.database_analyzer import DatabaseAnalyzer
from app.services.api_converter import APIConverter
from app.services.behavioral_validation import BehavioralValidationEngine
from app.agents.orchestrator import CodeMorphOrchestrator

client = TestClient(app)


class TestDatabaseAnalysis:
    """Test database analysis functionality."""
    
    def test_start_database_analysis(self):
        """Test starting database analysis."""
        with patch('app.api.enhanced_analysis.database_analyzer') as mock_analyzer:
            mock_analyzer.analyze_database_files.return_value = {
                "schemas": [],
                "orm_models": {},
                "analysis": {"total_schemas": 0},
                "recommendations": []
            }
            
            response = client.post("/api/enhanced/database-analysis/test-project")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Database analysis started"
            assert data["project_id"] == "test-project"
            assert data["status"] == "processing"
    
    def test_get_database_analysis_results(self):
        """Test getting database analysis results."""
        with patch('app.api.enhanced_analysis._get_stored_database_results') as mock_get:
            mock_get.return_value = {
                "schemas": [{
                    "name": "test_schema",
                    "database_type": "mysql",
                    "tables": [{
                        "name": "users",
                        "columns": [{
                            "name": "id",
                            "type": "integer",
                            "nullable": False,
                            "primary_key": True,
                            "foreign_key": None,
                            "default_value": None,
                            "max_length": None,
                            "precision": None,
                            "scale": None,
                            "auto_increment": True,
                            "unique": False,
                            "comment": None
                        }],
                        "primary_keys": ["id"],
                        "foreign_keys": [],
                        "indexes": [],
                        "comment": None,
                        "engine": "InnoDB",
                        "charset": "utf8"
                    }],
                    "views": [],
                    "procedures": [],
                    "functions": [],
                    "triggers": []
                }],
                "orm_models": {"User.py": "class User(Base): pass"},
                "analysis": {
                    "total_schemas": 1,
                    "total_tables": 1,
                    "total_columns": 1,
                    "total_indexes": 0,
                    "total_foreign_keys": 0,
                    "primary_database_type": "mysql",
                    "relationship_analysis": {
                        "total_relationships": 0,
                        "isolated_tables": 1,
                        "highly_connected_tables": 0,
                        "relationship_graph": {}
                    },
                    "type_analysis": {
                        "type_distribution": {"integer": 1},
                        "most_common_type": "integer",
                        "total_columns": 1
                    },
                    "complexity_score": 0.1
                },
                "recommendations": []
            }
            
            response = client.get("/api/enhanced/database-analysis/test-project/results")
            assert response.status_code == 200
            data = response.json()
            assert len(data["schemas"]) == 1
            assert data["schemas"][0]["name"] == "test_schema"
            assert len(data["orm_models"]) == 1


class TestAPIAnalysis:
    """Test API analysis functionality."""
    
    def test_start_api_analysis(self):
        """Test starting API analysis."""
        with patch('app.api.enhanced_analysis.api_converter') as mock_converter:
            mock_converter.convert_api_files.return_value = {
                "endpoints": [],
                "models": [],
                "frameworks": [],
                "openapi_spec": {},
                "statistics": {"total_endpoints": 0}
            }
            
            response = client.post("/api/enhanced/api-analysis/test-project")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "API analysis started"
            assert data["project_id"] == "test-project"
            assert data["status"] == "processing"
    
    def test_get_api_analysis_results(self):
        """Test getting API analysis results."""
        with patch('app.api.enhanced_analysis._get_stored_api_results') as mock_get:
            mock_get.return_value = {
                "endpoints": [{
                    "path": "/users",
                    "method": "GET",
                    "function_name": "get_users",
                    "parameters": [],
                    "responses": [{
                        "status_code": 200,
                        "description": "Success",
                        "content_type": "application/json",
                        "schema": None,
                        "examples": None
                    }],
                    "summary": None,
                    "description": None,
                    "tags": [],
                    "deprecated": False,
                    "security": None,
                    "file_path": "app/api/users.py",
                    "line_number": 10
                }],
                "models": [],
                "frameworks": ["flask"],
                "openapi_spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "Test API", "version": "1.0.0"},
                    "paths": {},
                    "components": {"schemas": {}}
                },
                "statistics": {
                    "total_endpoints": 1,
                    "total_models": 0,
                    "methods_distribution": {"GET": 1},
                    "unique_paths": 1,
                    "parameters_total": 0,
                    "avg_parameters_per_endpoint": 0.0
                },
                "postman_collection": {
                    "info": {"name": "Test Collection"},
                    "item": []
                },
                "curl_examples": [],
                "conversion_summary": {
                    "endpoints_converted": 1,
                    "models_extracted": 0,
                    "frameworks_detected": ["flask"],
                    "openapi_generated": True,
                    "postman_collection_generated": True,
                    "curl_examples_generated": True
                }
            }
            
            response = client.get("/api/enhanced/api-analysis/test-project/results")
            assert response.status_code == 200
            data = response.json()
            assert len(data["endpoints"]) == 1
            assert data["endpoints"][0]["path"] == "/users"
            assert data["frameworks"] == ["flask"]


class TestValidationDashboard:
    """Test validation dashboard functionality."""
    
    def test_get_validation_dashboard(self):
        """Test getting validation dashboard."""
        with patch('app.api.enhanced_analysis.validation_engine') as mock_engine:
            mock_engine.get_review_dashboard.return_value = {
                "pending_reviews": [],
                "pending_count": 0,
                "priority_distribution": {},
                "timed_out_reviews": [],
                "review_history_count": 0,
                "statistics": {
                    "total_reviews_created": 0,
                    "completed_reviews": 0,
                    "timeout_rate": 0.0
                }
            }
            
            response = client.get("/api/enhanced/validation/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert data["pending_count"] == 0
            assert data["pending_reviews"] == []
    
    def test_submit_review_decision(self):
        """Test submitting review decision."""
        with patch('app.api.enhanced_analysis.validation_engine') as mock_engine:
            mock_engine.submit_review_decision.return_value = {
                "success": True,
                "message": "Review decision submitted successfully",
                "request_id": "test-request",
                "decision": "approved",
                "reviewer": "test-reviewer"
            }
            
            response = client.post("/api/enhanced/validation/review/test-request", json={
                "decision": "approved",
                "reviewer": "test-reviewer",
                "notes": "Looks good",
                "decision_reason": "All validations passed"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["decision"] == "approved"
    
    def test_get_validation_metrics(self):
        """Test getting validation metrics."""
        with patch('app.api.enhanced_analysis.validation_engine') as mock_engine:
            mock_engine.get_validation_metrics.return_value = {
                "total_validations": 10,
                "approval_rate": 0.8,
                "average_review_time_minutes": 15.5,
                "rule_type_distribution": {
                    "confidence_threshold": 5,
                    "security_check": 3,
                    "architecture_compliance": 2
                },
                "priority_distribution": {
                    "high": 2,
                    "medium": 5,
                    "low": 3
                },
                "reviewer_statistics": {
                    "reviewer1": {"total": 5, "approved": 4, "rejected": 1}
                },
                "current_pending": 2
            }
            
            response = client.get("/api/enhanced/validation/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["total_validations"] == 10
            assert data["approval_rate"] == 0.8


class TestOrchestrator:
    """Test orchestrator functionality."""
    
    def test_get_orchestrator_status(self):
        """Test getting orchestrator status."""
        with patch('app.api.enhanced_analysis._get_orchestrator_status') as mock_get:
            mock_get.return_value = {
                "project_id": "test-project",
                "current_step": "completed",
                "completed_steps": [
                    "initialize",
                    "context_analysis",
                    "code_analysis",
                    "dependency_analysis",
                    "database_analysis",
                    "api_analysis",
                    "confidence_scoring"
                ],
                "status": "completed",
                "confidence_scores": {
                    "overall": 0.85,
                    "analysis": 0.9,
                    "context": 0.8,
                    "database": 0.7,
                    "api": 0.9
                },
                "validation_status": "approved"
            }
            
            response = client.get("/api/enhanced/orchestrator/test-project/status")
            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == "test-project"
            assert data["status"] == "completed"
            assert len(data["completed_steps"]) == 7


class TestIntegrationWorkflow:
    """Test end-to-end integration workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self):
        """Test complete analysis workflow integration."""
        # Mock all services
        with patch('app.services.database_analyzer.DatabaseAnalyzer') as mock_db_analyzer, \
             patch('app.services.api_converter.APIConverter') as mock_api_converter, \
             patch('app.services.behavioral_validation.BehavioralValidationEngine') as mock_validation, \
             patch('app.services.confidence_scoring.ConfidenceScoringEngine') as mock_confidence:
            
            # Setup mocks
            mock_db_analyzer.return_value.analyze_database_files.return_value = {
                "schemas": [], "orm_models": {}, "analysis": {}, "recommendations": []
            }
            mock_api_converter.return_value.convert_api_files.return_value = {
                "endpoints": [], "models": [], "frameworks": [], "openapi_spec": {}, "statistics": {}
            }
            mock_validation.return_value.validate_analysis_results.return_value = {
                "validation_results": [], "overall_status": "approved", "review_request": None
            }
            mock_confidence.return_value.calculate_comprehensive_confidence.return_value = {}
            
            # Create orchestrator
            orchestrator = CodeMorphOrchestrator()
            
            # Test data
            test_files = [{
                "path": "test.py",
                "content": "def hello(): pass",
                "language": "python",
                "size": 100
            }]
            
            input_data = {
                "files": test_files,
                "project_id": "test-project"
            }
            
            # Run orchestration
            result = await orchestrator.orchestrate(
                files=test_files,
                project_context={"project_id": "test-project"}
            )
            
            # Verify result structure
            assert "analysis_results" in result
            assert "context_results" in result
            assert "confidence_scores" in result
            assert "validation_results" in result
    
    def test_error_handling(self):
        """Test error handling in API endpoints."""
        # Test with non-existent project
        response = client.get("/api/enhanced/database-analysis/non-existent/results")
        assert response.status_code == 404
        
        # Test invalid validation decision
        response = client.post("/api/enhanced/validation/review/test-request", json={
            "decision": "invalid_decision",
            "reviewer": "test-reviewer"
        })
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    path: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    path: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    total_files: int
    total_loc: int
    languages_count: int
    frameworks_count: int
    language_distribution: Optional[dict] = None
    architecture_layers: Optional[dict] = None
    detected_apis: Optional[list] = None
    detected_tables: Optional[list] = None
    detected_stack: Optional[list] = None
    recommendations: Optional[list] = None
    selected_stack: Optional[dict] = None
    transformation_progress: Optional[dict] = None
    transformation_mappings: Optional[list] = None
    project_summary: str = ""
    test_scripts: Optional[list] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectSummary(BaseModel):
    id: str
    name: str
    path: str
    description: str
    status: str
    created_at: datetime
    total_files: int
    total_loc: int

    class Config:
        from_attributes = True


class PipelineStatus(BaseModel):
    project_id: str
    status: str
    stage: str
    progress: float
    message: str


class StackSelection(BaseModel):
    selections: dict[str, str]  # category -> chosen technology


class TransformationMapping(BaseModel):
    source: str
    target: str
    file_count: int
    status: str  # pending, active, completed


# Enhanced Analysis Schemas

class DatabaseTable(BaseModel):
    name: str
    columns: list[dict]
    primary_keys: list[str]
    foreign_keys: list[dict]
    indexes: list[dict]
    comment: Optional[str] = None
    engine: Optional[str] = None
    charset: Optional[str] = None


class DatabaseAnalysis(BaseModel):
    id: str
    project_id: str
    database_type: str
    schema_name: str
    tables_count: int
    views_count: int
    procedures_count: int
    functions_count: int
    triggers_count: int
    tables_data: list[DatabaseTable]
    relationships: list[dict]
    indexes: list[dict]
    orm_models: dict
    recommendations: list[dict]
    complexity_metrics: dict
    old_schema: dict
    new_schema: dict
    migration_scripts: list[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIEndpointDetail(BaseModel):
    path: str
    method: str
    function_name: str
    parameters: list[dict]
    responses: list[dict]
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = []
    deprecated: bool = False
    security: Optional[list[str]] = None
    file_path: str = ""
    line_number: int = 0


class APIModel(BaseModel):
    name: str
    properties: dict[str, dict]
    required_fields: list[str]
    description: Optional[str] = None
    example: Optional[dict] = None


class APIAnalysis(BaseModel):
    id: str
    project_id: str
    framework_type: str
    endpoints_count: int
    models_count: int
    endpoints_data: list[APIEndpointDetail]
    models_data: list[APIModel]
    openapi_spec: dict
    postman_collection: dict
    curl_examples: list[str]
    old_framework: Optional[str] = None
    new_framework: Optional[str] = None
    conversion_mappings: list[dict]
    statistics: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ValidationDecision(BaseModel):
    decision: str  # approved, rejected
    reviewer: str
    notes: str
    reason: str


class ValidationMetrics(BaseModel):
    total_validations: int
    pending_reviews: int
    approved_count: int
    rejected_count: int
    approval_rate: float
    average_review_time: float


class ReviewRequest(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    context_data: dict
    review_notes: Optional[str] = None
    decision_reason: Optional[str] = None

    class Config:
        from_attributes = True


class ValidationDashboard(BaseModel):
    pending_reviews: list[ReviewRequest]
    recent_decisions: list[dict]
    metrics: ValidationMetrics
    validation_results: list[dict]

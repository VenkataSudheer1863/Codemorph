import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from app.database.db import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


PIPELINE_STAGES = [
    "created",
    "ingesting",
    "parsing",
    "context_building",
    "agentic_analysis",
    "selecting",
    "transforming",
    "post_transformation_analysis",
    "complete",
]


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    path = Column(Text, nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="created")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Ingestion stats
    total_files = Column(Integer, default=0)
    total_loc = Column(Integer, default=0)
    languages_count = Column(Integer, default=0)
    frameworks_count = Column(Integer, default=0)

    # JSON data fields
    language_distribution = Column(JSON, default=dict)
    architecture_layers = Column(JSON, default=dict)
    detected_apis = Column(JSON, default=list)
    detected_tables = Column(JSON, default=list)
    detected_stack = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    selected_stack = Column(JSON, default=dict)
    transformation_progress = Column(JSON, default=dict)
    transformation_mappings = Column(JSON, default=list)
    project_summary = Column(Text, default="")
    test_scripts = Column(JSON, default=list)

    # Error tracking
    error_message = Column(Text, nullable=True)

    pipeline_runs = relationship("PipelineRun", back_populates="project", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")
    parsed_files = relationship("ParsedFile", back_populates="project", cascade="all, delete-orphan")
    context_elements = relationship("ContextElement", back_populates="project", cascade="all, delete-orphan")
    transformed_files = relationship("TransformedFile", back_populates="project", cascade="all, delete-orphan")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    stage = Column(String(50), default="created")
    progress = Column(Float, default=0.0)
    message = Column(Text, default="")
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="pipeline_runs")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    result_type = Column(String(50), nullable=False)  # ingestion, parsing, analysis, stack, etc.
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="analysis_results")


class ParsedFile(Base):
    __tablename__ = "parsed_files"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)  # e.g., 'javascript', 'python', 'java'
    language = Column(String(50), nullable=False)
    framework = Column(String(100), nullable=True)
    
    # AST and parsing data
    ast_data = Column(JSON, default=dict)  # Full AST representation
    functions = Column(JSON, default=list)  # Extracted functions
    classes = Column(JSON, default=list)   # Extracted classes
    imports = Column(JSON, default=list)   # Import statements
    exports = Column(JSON, default=list)   # Export statements
    variables = Column(JSON, default=list) # Global variables
    
    # Code metrics
    lines_of_code = Column(Integer, default=0)
    complexity_score = Column(Float, default=0.0)
    maintainability_index = Column(Float, default=0.0)
    
    # Content and metadata
    original_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA256 hash
    
    # Parsing status
    parsing_successful = Column(Boolean, default=True)
    parsing_errors = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="parsed_files")


class ContextElement(Base):
    __tablename__ = "context_elements"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Element identification
    element_type = Column(String(50), nullable=False)  # 'component', 'service', 'model', 'api', 'database'
    element_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    
    # Architecture layer
    layer = Column(String(100), nullable=False)  # 'frontend', 'backend', 'database', 'config'
    
    # Element details
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list)  # Technologies used in this element
    dependencies = Column(JSON, default=list)  # Dependencies on other elements
    dependents = Column(JSON, default=list)    # Elements that depend on this
    
    # Code analysis
    code_patterns = Column(JSON, default=list)  # Detected patterns
    api_endpoints = Column(JSON, default=list)  # If it's an API component
    database_entities = Column(JSON, default=list)  # If it's a database component
    
    # Metadata
    confidence_score = Column(Float, default=0.0)  # Confidence in the analysis
    complexity_level = Column(String(20), default="medium")  # low, medium, high
    
    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="context_elements")


class DatabaseAnalysisResult(Base):
    __tablename__ = "database_analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    database_type = Column(String(50), nullable=False)  # mysql, postgresql, etc.
    schema_name = Column(String(255), nullable=False)
    tables_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    procedures_count = Column(Integer, default=0)
    functions_count = Column(Integer, default=0)
    triggers_count = Column(Integer, default=0)
    
    # Analysis results
    tables_data = Column(JSON, default=list)  # Table definitions
    relationships = Column(JSON, default=list)  # Foreign key relationships
    indexes = Column(JSON, default=list)  # Index definitions
    orm_models = Column(JSON, default=dict)  # Generated ORM models
    recommendations = Column(JSON, default=list)  # Improvement recommendations
    complexity_metrics = Column(JSON, default=dict)  # Complexity analysis
    
    # Comparison data for old vs new
    old_schema = Column(JSON, default=dict)
    new_schema = Column(JSON, default=dict)
    migration_scripts = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project")


class APIAnalysisResult(Base):
    __tablename__ = "api_analysis_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    framework_type = Column(String(50), nullable=False)  # spring_boot, flask, etc.
    endpoints_count = Column(Integer, default=0)
    models_count = Column(Integer, default=0)
    
    # Analysis results
    endpoints_data = Column(JSON, default=list)  # Endpoint definitions
    models_data = Column(JSON, default=list)  # Data model definitions
    openapi_spec = Column(JSON, default=dict)  # Generated OpenAPI spec
    postman_collection = Column(JSON, default=dict)  # Postman collection
    curl_examples = Column(JSON, default=list)  # cURL examples
    
    # Framework comparison
    old_framework = Column(String(50), nullable=True)
    new_framework = Column(String(50), nullable=True)
    conversion_mappings = Column(JSON, default=list)  # Framework conversion mappings
    
    # Statistics
    statistics = Column(JSON, default=dict)  # API statistics
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    validation_type = Column(String(50), nullable=False)  # confidence, security, architecture, etc.
    status = Column(String(20), nullable=False)  # pending, approved, rejected, etc.
    score = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    
    # Validation details
    message = Column(Text, nullable=True)
    evidence = Column(JSON, default=list)  # Evidence supporting the result
    recommendations = Column(JSON, default=list)  # Recommendations for improvement
    
    # Review information
    reviewer = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project")


class ReviewRequest(Base):
    __tablename__ = "review_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="pending")  # pending, approved, rejected, timeout
    
    # Assignment and timing
    assigned_to = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Review data
    context_data = Column(JSON, default=dict)
    review_notes = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    project = relationship("Project")


class TransformedFile(Base):
    """Stores each file produced by the transformation stage with its computed metrics."""
    __tablename__ = "transformed_files"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)

    # File identity
    file_path = Column(Text, nullable=False)          # path in the converted codebase
    language = Column(String(50), default="unknown")
    framework = Column(String(100), nullable=True)

    # Content
    content = Column(Text, nullable=True)             # full transformed source
    content_hash = Column(String(64), nullable=True)  # SHA-256 of content

    # Metrics computed from content at save time
    lines_of_code = Column(Integer, default=0)
    cyclomatic_complexity = Column(Float, default=0.0)  # McCabe proxy
    maintainability_index = Column(Float, default=0.0)  # Halstead-inspired proxy (0-100)
    todo_count = Column(Integer, default=0)             # TODO/FIXME markers
    syntax_error_flag = Column(Boolean, default=False)  # unbalanced braces/parens
    is_passthrough = Column(Boolean, default=False)     # file was not truly transformed

    # Parsed structure (re-parsed after transformation)
    functions = Column(JSON, default=list)
    classes = Column(JSON, default=list)
    imports = Column(JSON, default=list)
    endpoints = Column(JSON, default=list)

    created_at = Column(DateTime, default=utcnow)

    project = relationship("Project", back_populates="transformed_files")

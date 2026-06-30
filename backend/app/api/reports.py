"""Reports API — PDF download endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.project import Project
from app.services.report_generator import generate_legacy_report, generate_migration_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["reports"])


@router.get("/{project_id}/report/legacy")
def download_legacy_report(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert SQLAlchemy model to dict for report generator
    project_data = {
        "name": project.name,
        "path": project.path,
        "description": project.description,
        "total_files": project.total_files,
        "total_loc": project.total_loc,
        "languages_count": project.languages_count,
        "frameworks_count": project.frameworks_count,
        "language_distribution": project.language_distribution or {},
        "architecture_layers": project.architecture_layers or {},
        "detected_apis": project.detected_apis or [],
        "detected_tables": project.detected_tables or [],
        "detected_stack": project.detected_stack or [],
    }

    try:
        pdf_bytes = generate_legacy_report(project_data)
    except Exception as e:
        logger.error(f"Failed to generate legacy report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{project.name}_legacy_analysis.pdf"',
        },
    )


@router.get("/{project_id}/report/migration")
def download_migration_report(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != "complete":
        raise HTTPException(status_code=400, detail="Migration report is only available after transformation is complete")

    project_data = {
        "name": project.name,
        "path": project.path,
        "selected_stack": project.selected_stack or {},
        "transformation_mappings": project.transformation_mappings or [],
        "recommendations": project.recommendations or [],
        "detected_stack": project.detected_stack or [],
    }

    try:
        pdf_bytes = generate_migration_report(project_data)
    except Exception as e:
        logger.error(f"Failed to generate migration report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{project.name}_migration_report.pdf"',
        },
    )

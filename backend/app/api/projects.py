"""Projects API — CRUD for projects."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.db import get_db
from app.models.project import Project
from app.models.schemas import ProjectCreate, ProjectResponse, ProjectSummary


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name,
        path=data.path,
        description=data.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Name cannot be empty")
        project.name = name
    if data.description is not None:
        project.description = data.description
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    import os
    import shutil
    import logging
    
    logger = logging.getLogger(__name__)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Clean up vector store files
    vector_store_path = f"data/vector_stores/{project_id}"
    if os.path.exists(vector_store_path):
        try:
            shutil.rmtree(vector_store_path)
            logger.info(f"Deleted vector store for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to delete vector store for project {project_id}: {e}")
    
    # Clean up any artifact files (from pipeline data)
    from app.api.pipeline import _pipeline_data
    if project_id in _pipeline_data:
        pipeline_data = _pipeline_data[project_id]
        artifact_zip = pipeline_data.get("artifact_zip")
        if artifact_zip and os.path.exists(artifact_zip):
            try:
                os.remove(artifact_zip)
                logger.info(f"Deleted artifact ZIP for project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to delete artifact ZIP for project {project_id}: {e}")
        
        # Remove from in-memory pipeline data
        del _pipeline_data[project_id]
        logger.info(f"Cleaned up pipeline data for project {project_id}")
    
    # Delete the project (cascade will handle related records)
    db.delete(project)
    db.commit()
    
    logger.info(f"Successfully deleted project {project_id}")
    return {"detail": "Project deleted"}

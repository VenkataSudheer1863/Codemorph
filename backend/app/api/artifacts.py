"""Artifacts API — ZIP download endpoint."""

import os
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.project import Project
from app.api.pipeline import _pipeline_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["artifacts"])


@router.get("/{project_id}/artifacts")
def download_artifacts(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != "complete":
        raise HTTPException(status_code=400, detail="Artifacts are only available after transformation is complete")

    data = _pipeline_data.get(project_id, {})
    zip_path = data.get("artifact_zip")

    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Artifact ZIP not found. Please re-run the transformation.")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{project.name}_modernized.zip",
    )

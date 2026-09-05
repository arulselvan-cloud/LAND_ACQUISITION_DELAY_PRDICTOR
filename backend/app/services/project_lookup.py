"""LandSight AI - Project Lookup and Resolution Service."""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.project import Project


def get_project_or_404(db: Session, identifier: str) -> Project:
    """Resolves a project by UUID string or project_code.
    
    Raises 404 HTTPException if not found.
    """
    proj: Optional[Project] = None
    try:
        proj_uuid = UUID(identifier)
        proj = db.query(Project).filter_by(id=proj_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not proj:
        proj = db.query(Project).filter_by(project_code=identifier).first()

    if not proj:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{identifier}' not found. Please verify the project UUID or project_code."
        )

    return proj

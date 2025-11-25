"""Mock resource endpoints for demonstrating authorization."""

from fastapi import APIRouter, Depends
from typing import List

from app.api.dependencies import require_permission
from app.models.mock_resources import (
    Document,
    Project,
    Report,
    MOCK_DOCUMENTS,
    MOCK_PROJECTS,
    MOCK_REPORTS
)

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.get(
    "/documents",
    response_model=List[dict],
    dependencies=[Depends(require_permission("documents", "read"))]
)
async def get_documents():
    """
    Get list of mock documents.
    
    Requires: documents:read permission
    
    Returns:
        List of document objects
        
    Requirements: 10.2, 10.3, 10.4
    """
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "author": doc.author,
            "created_at": doc.created_at.isoformat()
        }
        for doc in MOCK_DOCUMENTS
    ]


@router.get(
    "/projects",
    response_model=List[dict],
    dependencies=[Depends(require_permission("projects", "read"))]
)
async def get_projects():
    """
    Get list of mock projects.
    
    Requires: projects:read permission
    
    Returns:
        List of project objects
        
    Requirements: 10.2, 10.3, 10.4
    """
    return [
        {
            "id": proj.id,
            "name": proj.name,
            "description": proj.description,
            "status": proj.status,
            "owner": proj.owner,
            "created_at": proj.created_at.isoformat()
        }
        for proj in MOCK_PROJECTS
    ]


@router.get(
    "/reports",
    response_model=List[dict],
    dependencies=[Depends(require_permission("reports", "read"))]
)
async def get_reports():
    """
    Get list of mock reports.
    
    Requires: reports:read permission
    
    Returns:
        List of report objects
        
    Requirements: 10.2, 10.3, 10.4
    """
    return [
        {
            "id": rep.id,
            "title": rep.title,
            "summary": rep.summary,
            "generated_by": rep.generated_by,
            "generated_at": rep.generated_at.isoformat()
        }
        for rep in MOCK_REPORTS
    ]

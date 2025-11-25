"""Mock resource data models for demonstrating authorization."""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Document:
    """Mock document resource."""
    id: int
    title: str
    content: str
    author: str
    created_at: datetime


@dataclass
class Project:
    """Mock project resource."""
    id: int
    name: str
    description: str
    status: str
    owner: str
    created_at: datetime


@dataclass
class Report:
    """Mock report resource."""
    id: int
    title: str
    summary: str
    generated_by: str
    generated_at: datetime


# In-memory collections with sample data
MOCK_DOCUMENTS: List[Document] = [
    Document(
        id=1,
        title="System Architecture Overview",
        content="This document describes the high-level architecture...",
        author="Alice Johnson",
        created_at=datetime(2024, 1, 15, 10, 30)
    ),
    Document(
        id=2,
        title="API Documentation",
        content="Complete API reference for all endpoints...",
        author="Bob Smith",
        created_at=datetime(2024, 2, 20, 14, 15)
    ),
    Document(
        id=3,
        title="Security Guidelines",
        content="Best practices for secure development...",
        author="Carol White",
        created_at=datetime(2024, 3, 10, 9, 0)
    ),
]

MOCK_PROJECTS: List[Project] = [
    Project(
        id=1,
        name="Authentication System",
        description="Custom auth backend with RBAC",
        status="active",
        owner="Alice Johnson",
        created_at=datetime(2024, 1, 5, 8, 0)
    ),
    Project(
        id=2,
        name="Data Analytics Platform",
        description="Real-time analytics and reporting",
        status="active",
        owner="Bob Smith",
        created_at=datetime(2024, 2, 1, 10, 0)
    ),
    Project(
        id=3,
        name="Mobile App",
        description="Cross-platform mobile application",
        status="planning",
        owner="Carol White",
        created_at=datetime(2024, 3, 15, 11, 30)
    ),
]

MOCK_REPORTS: List[Report] = [
    Report(
        id=1,
        title="Monthly User Activity Report",
        summary="User engagement metrics for March 2024",
        generated_by="System",
        generated_at=datetime(2024, 4, 1, 0, 0)
    ),
    Report(
        id=2,
        title="Security Audit Report",
        summary="Quarterly security assessment results",
        generated_by="Security Team",
        generated_at=datetime(2024, 3, 31, 18, 0)
    ),
    Report(
        id=3,
        title="Performance Metrics",
        summary="System performance analysis for Q1 2024",
        generated_by="DevOps Team",
        generated_at=datetime(2024, 4, 5, 12, 0)
    ),
]

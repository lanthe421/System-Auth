# Authorization Middleware Usage Guide

This document explains how to use the authorization middleware dependencies in your FastAPI endpoints.

## Available Dependencies

### 1. `get_current_user`
Validates the authentication token and returns the current user.

**Usage:**
```python
from fastapi import Depends
from app.api.dependencies import get_current_user
from app.models.user import User

@app.get("/api/users/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": f"{current_user.first_name} {current_user.last_name}"
    }
```

**Returns:** 
- 200: The authenticated user
- 401: If token is missing, invalid, or expired

---

### 2. `require_permission(resource, action)`
Checks if the current user has a specific permission (via role or direct grant).

**Usage:**
```python
from fastapi import Depends
from app.api.dependencies import require_permission

@app.get("/api/resources/documents", dependencies=[Depends(require_permission("documents", "read"))])
async def get_documents():
    return {"documents": ["doc1", "doc2", "doc3"]}

@app.post("/api/resources/documents", dependencies=[Depends(require_permission("documents", "create"))])
async def create_document(data: dict):
    return {"message": "Document created"}
```

**Returns:**
- 200: If user has the required permission
- 401: If user is not authenticated
- 403: If user lacks the required permission

**Note:** This is a dependency factory - you call it with the resource and action, and it returns a dependency function.

---

### 3. `require_admin`
Checks if the current user has the "admin" role.

**Usage:**
```python
from fastapi import Depends
from app.api.dependencies import require_admin

@app.get("/api/admin/roles", dependencies=[Depends(require_admin)])
async def get_all_roles():
    return {"roles": [...]}

@app.post("/api/admin/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_admin)])
async def assign_role(user_id: int, role_id: int):
    return {"message": "Role assigned"}
```

**Returns:**
- 200: If user has admin role
- 401: If user is not authenticated
- 403: If user is not an admin

---

## Combining Dependencies

You can combine multiple dependencies in a single endpoint:

```python
from fastapi import Depends
from app.api.dependencies import get_current_user, require_permission
from app.models.user import User

@app.put("/api/resources/documents/{doc_id}")
async def update_document(
    doc_id: int,
    data: dict,
    current_user: User = Depends(require_permission("documents", "update"))
):
    # current_user is available here and has been verified to have the permission
    return {"message": f"Document {doc_id} updated by {current_user.email}"}
```

---

## Permission Checking Logic

The `require_permission` dependency checks permissions from two sources:

1. **Role-based permissions**: Permissions granted through roles assigned to the user
2. **Direct permissions**: Permissions granted directly to the user

If the user has the permission from either source, access is granted.

---

## Admin Role Checking

The `require_admin` dependency checks if the user has a role named "admin" (case-insensitive). This means:
- "admin" ✓
- "Admin" ✓
- "ADMIN" ✓
- "administrator" ✗ (must be exactly "admin")

---

## Error Responses

All authorization errors return consistent JSON responses:

**401 Unauthorized:**
```json
{
    "detail": "Missing authorization header"
}
```

**403 Forbidden:**
```json
{
    "detail": "User lacks required permission: documents:read"
}
```

or

```json
{
    "detail": "Admin role required to access this resource"
}
```

---

## Testing

Example test for an endpoint with authorization:

```python
import pytest
from fastapi.testclient import TestClient

def test_protected_endpoint_with_permission(client: TestClient, auth_token: str):
    """Test accessing a protected endpoint with valid permission."""
    response = client.get(
        "/api/resources/documents",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_protected_endpoint_without_permission(client: TestClient, auth_token: str):
    """Test accessing a protected endpoint without permission."""
    response = client.get(
        "/api/resources/documents",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 403
```

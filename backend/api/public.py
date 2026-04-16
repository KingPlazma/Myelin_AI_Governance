"""
Public-facing utility endpoints for frontend demo flows.
Sensitive provisioning logic is handled server-side.
"""

import secrets
import shutil
import tempfile
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.config.database import get_db
from backend.models.user import UserCreate, UserRole
from backend.models.api_key import APIKeyCreate
from backend.services.auth_service import get_auth_service

router = APIRouter(prefix="/public", tags=["Public"])


class DemoKeyRequest(BaseModel):
    """Request model for demo API key provisioning."""
    full_name: Optional[str] = Field(default="Myelin Demo User")
    organization_name: Optional[str] = Field(default=None)


@router.post("/demo-api-key")
async def create_demo_api_key(payload: DemoKeyRequest):
    """
    Create a demo user and return an API key from server-side logic.
    This avoids exposing registration internals in client-side code.
    """
    if not settings.PUBLIC_DEMO_KEY_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo key provisioning is disabled"
        )

    if settings.PUBLIC_DEMO_API_KEY:
        return {
            "api_key": settings.PUBLIC_DEMO_API_KEY,
            "key_prefix": settings.PUBLIC_DEMO_API_KEY[:20],
            "organization_id": "demo-org",
            "email": "demo@myelin.local",
            "mode": "local-demo"
        }

    suffix = secrets.token_hex(4)
    email = f"demo_{suffix}@example.com"
    password = secrets.token_urlsafe(18) + "A1!"
    org_name = payload.organization_name or f"Demo Org {suffix}"

    auth_service = get_auth_service()
    db = get_db()

    user, organization = await auth_service.register_user(
        UserCreate.model_validate({
            "email": email,
            "password": password,
            "full_name": payload.full_name,
            "organization_name": org_name,
            "role": UserRole.DEVELOPER,
        })
    )

    # Mark demo accounts as verified so demo keys can be used immediately.
    await db.mark_user_email_verified(user["id"])

    api_key, api_key_record = await auth_service.create_api_key(
        user_id=user["id"],
        organization_id=organization["id"],
        key_data=APIKeyCreate.model_validate({
            "name": "Demo Web Key",
            "expires_in_days": None,
        })
    )

    return {
        "api_key": api_key,
        "key_prefix": api_key_record["key_prefix"],
        "organization_id": organization["id"],
        "email": user["email"]
    }


@router.get("/download-extension")
async def download_extension(background_tasks: BackgroundTasks):
    """Zip the extension folder and serve it as a download."""
    # Resolve project root relative to this file
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    extension_path = os.path.join(project_root, "extension")
    
    if not os.path.exists(extension_path):
        raise HTTPException(status_code=404, detail=f"Extension folder not found at {extension_path}")
        
    # Create temporary directory to store the zip
    temp_dir = tempfile.mkdtemp()
    zip_base_name = os.path.join(temp_dir, "myelin-extension")
    
    # Create zip archive
    zip_path = shutil.make_archive(zip_base_name, 'zip', extension_path)
    
    # Define cleanup to run after response is sent
    def cleanup():
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
    background_tasks.add_task(cleanup)
    
    return FileResponse(
        path=zip_path,
        filename="myelin-extension.zip",
        media_type="application/zip"
    )

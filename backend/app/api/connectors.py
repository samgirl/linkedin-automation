import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.connector import Connection
from app.utils.token import get_current_user
from app.utils.crypto import encrypt_token, decrypt_token

settings = get_settings()
router = APIRouter(prefix="/api/connectors", tags=["connectors"])


class APIKeyRequest(BaseModel):
    api_key: str


class ManualImportRequest(BaseModel):
    provider: str
    data: str
    filename: str = ""


@router.get("/")
async def list_connectors(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.user_id == user.id)
    )
    connections = result.scalars().all()
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "status": c.status,
            "profile_data": c.profile_data,
            "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
            "has_api_key": bool(c.api_key_encrypted),
            "has_oauth": bool(c.access_token_encrypted),
        }
        for c in connections
    ]


@router.post("/linkedin/connect")
async def linkedin_connect(code: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import httpx
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.linkedin_redirect_uri,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange LinkedIn code")
        tokens = token_resp.json()

        profile_resp = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        profile = profile_resp.json()

    result = await db.execute(
        select(Connection).where(Connection.user_id == user.id, Connection.provider == "linkedin")
    )
    conn = result.scalar_one_or_none()
    if not conn:
        conn = Connection(user_id=user.id, provider="linkedin")
        db.add(conn)

    conn.access_token_encrypted = encrypt_token(tokens.get("access_token", ""))
    conn.refresh_token_encrypted = encrypt_token(tokens.get("refresh_token", ""))
    conn.provider_user_id = profile.get("sub")
    conn.provider_email = profile.get("email")
    conn.profile_data = profile

    return {"status": "connected", "provider": "linkedin"}


@router.post("/chatgpt/connect")
async def chatgpt_connect(req: APIKeyRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.user_id == user.id, Connection.provider == "chatgpt")
    )
    conn = result.scalar_one_or_none()
    if not conn:
        conn = Connection(user_id=user.id, provider="chatgpt")
        db.add(conn)

    conn.api_key_encrypted = encrypt_token(req.api_key)
    conn.status = "active"
    return {"status": "connected", "provider": "chatgpt"}


@router.post("/claude/connect")
async def claude_connect(req: APIKeyRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.user_id == user.id, Connection.provider == "claude")
    )
    conn = result.scalar_one_or_none()
    if not conn:
        conn = Connection(user_id=user.id, provider="claude")
        db.add(conn)

    conn.api_key_encrypted = encrypt_token(req.api_key)
    conn.status = "active"
    return {"status": "connected", "provider": "claude"}


@router.post("/import")
async def manual_import(req: ManualImportRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services.context_engine import ContextEngine
    engine = ContextEngine(db)

    if req.provider == "chatgpt":
        events = await engine.import_chatgpt_export(req.data, user.id)
    elif req.provider == "claude":
        events = await engine.import_claude_export(req.data, user.id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")

    return {"status": "imported", "events_created": len(events)}


@router.post("/{connection_id}/sync")
async def sync_connection(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Connection).where(Connection.id == connection_id, Connection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    from app.utils.helpers import utcnow
    conn.last_synced_at = utcnow()
    return {"status": "synced", "provider": conn.provider}


@router.delete("/{connection_id}")
async def disconnect(connection_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Connection).where(Connection.id == connection_id, Connection.user_id == user.id)
    )
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    await db.delete(conn)
    return {"status": "disconnected"}

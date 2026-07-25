import secrets
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import httpx

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.utils.token import create_access_token, create_refresh_token, decode_token, get_current_user
from app.utils.crypto import encrypt_token, decrypt_token, hash_password, verify_password

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


class EmailRegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class EmailLoginRequest(BaseModel):
    email: str
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


def _user_dict(user: User) -> dict:
    return {"id": user.id, "email": user.email, "name": user.name, "avatar_url": user.avatar_url}


@router.post("/register", response_model=AuthResponse)
async def register(req: EmailRegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=req.email, name=req.name, password_hash=hash_password(req.password))
    db.add(user)
    await db.flush()

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_dict(user))


@router.post("/login", response_model=AuthResponse)
async def login(req: EmailLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_dict(user))


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return AuthResponse(access_token=access, refresh_token=refresh, user=_user_dict(user))


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return _user_dict(user)


# --- LinkedIn OAuth ---
@router.get("/linkedin")
async def linkedin_login():
    state = secrets.token_urlsafe(32)
    url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={settings.linkedin_client_id}"
        f"&redirect_uri={settings.linkedin_redirect_uri}"
        f"&scope=openid%20profile%20email%20w_member_social"
        f"&state={state}"
    )
    return {"url": url, "state": state}


# --- Google OAuth ---
@router.get("/google")
async def google_login():
    state = secrets.token_urlsafe(32)
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&scope=openid%20email%20profile%20https://www.googleapis.com/auth/calendar.readonly"
        f"&state={state}&access_type=offline&prompt=consent"
    )
    return {"url": url, "state": state}


@router.get("/callback/google")
async def google_callback(code: str = "", state: str = "", db: AsyncSession = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        tokens = token_resp.json()

        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_info_resp.json()

    email = user_info.get("email")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            name=user_info.get("name", ""),
            avatar_url=user_info.get("picture"),
        )
        db.add(user)
        await db.flush()

    from app.models.connector import Connection
    conn_result = await db.execute(
        select(Connection).where(Connection.user_id == user.id, Connection.provider == "google")
    )
    conn = conn_result.scalar_one_or_none()
    if not conn:
        conn = Connection(user_id=user.id, provider="google")
        db.add(conn)

    conn.access_token_encrypted = encrypt_token(tokens.get("access_token", ""))
    conn.refresh_token_encrypted = encrypt_token(tokens.get("refresh_token", ""))
    conn.provider_user_id = user_info.get("id")
    conn.provider_email = email
    conn.profile_data = user_info

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    redirect = RedirectResponse(f"{settings.frontend_url}/auth/callback?access={access}&refresh={refresh}")
    return redirect

import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import httpx

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.connector import Connection
from app.utils.token import create_access_token, create_refresh_token, decode_token, get_current_user
from app.utils.crypto import encrypt_token, decrypt_token, hash_password, verify_password

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _error_page(title: str, detail: str) -> HTMLResponse:
    """Return a user-friendly HTML error page that auto-redirects."""
    html = f"""<!DOCTYPE html>
<html><head><title>PROS Auth</title></head>
<body style="font-family:system-ui;max-width:500px;margin:60px auto;text-align:center;background:#111;color:#eee;padding:20px;">
<h2>{title}</h2>
<p style="color:#aaa;">{detail}</p>
<p style="margin-top:30px;"><a href="{settings.frontend_url}/login" style="color:#818cf8;">← Back to PROS</a></p>
<script>setTimeout(function(){{ window.location.href = '{settings.frontend_url}/login'; }}, 5000);</script>
</body></html>"""
    return HTMLResponse(content=html)


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

    try:
        hashed = hash_password(req.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password hashing failed: {type(e).__name__}: {e}")

    user = User(email=req.email, name=req.name, password_hash=hashed)
    db.add(user)
    try:
        await db.flush()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database error: {type(e).__name__}: {e}")

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
    if not settings.linkedin_client_id:
        raise HTTPException(status_code=503, detail="LinkedIn login is not configured. The server is missing LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET.")
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
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google login is not configured. The server is missing GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    state = secrets.token_urlsafe(32)
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&scope=openid%20email%20profile"
        f"&state={state}&access_type=offline&prompt=consent"
    )
    return {"url": url, "state": state}


@router.get("/callback/google")
async def google_callback(code: str = "", state: str = "", error: str = "", db: AsyncSession = Depends(get_db)):
    if error:
        logger.error(f"Google OAuth error: {error}")
        return _error_page("Google Login Failed", f"Google returned an error: {error}. You may need to add yourself as a test user in Google Cloud Console.")

    if not code:
        return _error_page("Google Login Failed", "No authorization code received from Google. Please try again.")

    if not settings.google_client_id or not settings.google_client_secret:
        return _error_page("Server Config Error", "Google OAuth is not configured on the server. GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing.")

    async with httpx.AsyncClient(timeout=30) as client:
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
            error_detail = token_resp.text
            logger.error(f"Google token exchange failed: {token_resp.status_code} — {error_detail}")
            return _error_page("Google Login Failed", f"Could not verify with Google (error {token_resp.status_code}). Make sure GOOGLE_CLIENT_SECRET is correct on the server. Technical: {error_detail[:200]}")
        tokens = token_resp.json()

        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_info_resp.json()

    email = user_info.get("email")
    if not email:
        return _error_page("Google Login Failed", "Google did not return an email address. Check your Google Cloud Console OAuth consent screen configuration.")

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
    conn.status = "active"

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    return RedirectResponse(f"{settings.frontend_url}/auth/callback?access={access}&refresh={refresh}")


@router.get("/callback/linkedin")
async def linkedin_callback(code: str = "", state: str = "", error: str = "", db: AsyncSession = Depends(get_db)):
    if error:
        logger.error(f"LinkedIn OAuth error: {error}")
        return _error_page("LinkedIn Login Failed", f"LinkedIn returned an error: {error}. Please try again.")

    if not code:
        return _error_page("LinkedIn Login Failed", "No authorization code received from LinkedIn. Please try again.")

    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        return _error_page("Server Config Error", "LinkedIn OAuth is not configured on the server. LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET is missing.")

    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "code": code,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
                "redirect_uri": settings.linkedin_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            error_detail = token_resp.text
            logger.error(f"LinkedIn token exchange failed: {token_resp.status_code} — {error_detail}")
            return _error_page("LinkedIn Login Failed", f"Could not verify with LinkedIn (error {token_resp.status_code}). Make sure LINKEDIN_CLIENT_SECRET is correct. Technical: {error_detail[:200]}")
        tokens = token_resp.json()

        profile_resp = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        profile = profile_resp.json()

    email = profile.get("email", "")
    if not email:
        return _error_page("LinkedIn Login Failed", "LinkedIn did not return an email address. Check your LinkedIn app permissions.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            name=profile.get("name", ""),
            avatar_url=profile.get("picture"),
        )
        db.add(user)
        await db.flush()

    conn_result = await db.execute(
        select(Connection).where(Connection.user_id == user.id, Connection.provider == "linkedin")
    )
    conn = conn_result.scalar_one_or_none()
    if not conn:
        conn = Connection(user_id=user.id, provider="linkedin")
        db.add(conn)

    conn.access_token_encrypted = encrypt_token(tokens.get("access_token", ""))
    conn.refresh_token_encrypted = encrypt_token(tokens.get("refresh_token", ""))
    conn.provider_user_id = profile.get("sub")
    conn.provider_email = email
    conn.profile_data = profile
    conn.status = "active"

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    return RedirectResponse(f"{settings.frontend_url}/auth/callback?access={access}&refresh={refresh}")

import base64
from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()

_pwd_context = None


def _get_pwd_context():
    global _pwd_context
    if _pwd_context is None:
        from passlib.context import CryptContext
        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return _pwd_context


def _get_fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        key = Fernet.generate_key().decode()
    if isinstance(key, str):
        key = key.encode()
    if len(key) < 32:
        import hashlib
        key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def hash_password(password: str) -> str:
    return _get_pwd_context().hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _get_pwd_context().verify(plain_password, hashed_password)

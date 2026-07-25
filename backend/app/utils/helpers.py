from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def safe_filename(filename: str) -> str:
    import re
    name = re.sub(r'[^\w\-.]', '_', filename)
    return name[:255]

"""Utility functions."""

import uuid
from datetime import datetime


def generate_id() -> str:
    """Generate a new UUID."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.utcnow()

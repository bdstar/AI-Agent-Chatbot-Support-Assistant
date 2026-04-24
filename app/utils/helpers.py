import os
import json
from typing import Optional
from datetime import datetime


def get_file_extension(filename: str) -> str:
    """Get the file extension in lowercase."""
    return os.path.splitext(filename)[1].lower()


def is_supported_document(filename: str) -> bool:
    """Check if a file type is supported for ingestion."""
    supported = {".pdf", ".txt", ".pptx", ".ppt", ".png", ".jpg", ".jpeg", ".md"}
    return get_file_extension(filename) in supported


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_timestamp(dt: datetime) -> str:
    """Format a datetime object for display."""
    now = datetime.now()
    diff = now - dt

    if diff.days == 0:
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    else:
        return dt.strftime("%b %d, %Y")


def safe_json_loads(text: str, default=None):
    """Safely parse a JSON string, returning default on failure."""
    if default is None:
        default = []
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default

"""Document history formatting helpers."""
from datetime import datetime


def format_timestamp(value: str) -> str:
    try:
        return datetime.fromisoformat(value).astimezone().strftime("%b %d, %Y · %I:%M %p")
    except (ValueError, TypeError):
        return value

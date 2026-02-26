"""Input sanitization — prevent XSS and injection attacks."""
import re
import html


def sanitize_text(text: str) -> str:
    """Sanitize text input: escape HTML, remove script tags, limit length."""
    if not text:
        return ""
    # HTML escape
    text = html.escape(text)
    # Remove any remaining script-like patterns
    text = re.sub(r'(?i)<\s*script[^>]*>.*?</\s*script\s*>', '', text)
    text = re.sub(r'(?i)javascript\s*:', '', text)
    text = re.sub(r'(?i)on\w+\s*=', '', text)
    # Limit length
    return text[:5000]


def sanitize_signal_text(text: str) -> str:
    """Sanitize signal original_text for safe display."""
    return sanitize_text(text)

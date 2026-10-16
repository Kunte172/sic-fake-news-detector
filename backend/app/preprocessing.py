"""The same deterministic cleanup must be used by training and inference."""

import re
import unicodedata

# Versioned Colab cleaner, shared with ml.src.audit_data. Keep clean_text below
# unchanged for baseline-v0 artifacts; swapping their preprocessing invalidates
# previous scores. Colab artifacts use body-only inputs and labels 0=Fake/1=Real.
from .colab_preprocessing import clean_source_markers as clean_colab_text


REUTERS_DATELINE = re.compile(
    r"^\s*(?:[A-Z][A-Z .,'/()&-]{1,90}\s+)?\(Reuters\)\s*[-–—:]\s*",
    flags=re.IGNORECASE,
)
LEADING_REUTERS = re.compile(r"^\s*Reuters\s*[-–—:]\s*", flags=re.IGNORECASE)
WHITESPACE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    """Remove known wire-service prefixes, then normalize whitespace.

    This is a limited baseline rule. DATA-02 audits other source cues.
    """
    text = unicodedata.normalize("NFKC", value or "")
    text = REUTERS_DATELINE.sub("", text, count=1)
    text = LEADING_REUTERS.sub("", text, count=1)
    return WHITESPACE.sub(" ", text).strip()


def article_text(title: str, body: str) -> str:
    return clean_text(" ".join(part for part in (clean_text(title), clean_text(body)) if part))

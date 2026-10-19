import re
import html
import unicodedata

REUTERS_DATELINE = re.compile(
    r"^\s*[^.!?\n]{0,120}?\(\s*Reuters\s*\)\s*[-–—:]\s*",
    flags=re.I
)

PHOTO_CREDIT = re.compile(
    r"\b(?:"
    r"featured\s+image\b|"
    r"(?:image|photo)\s+credits?\s*[:\-]|"
    r"(?:image|photo)\s+(?:via|courtesy\s+of)\b"
    r")",
    flags=re.I
)

WEB_LINK = re.compile(
    r"(?:https?://|www\.|pic\.twitter\.com/|youtu\.be/)"
    r"[^\s<>\"“”]+",
    flags=re.I
)

def clean_source_markers(value):
    text = unicodedata.normalize("NFKC", html.unescape(str(value)))

    text = REUTERS_DATELINE.sub("", text, count=1)

    tail_start = max(0, len(text) - 300)
    credit = PHOTO_CREDIT.search(text, pos=tail_start)
    if credit:
        text = text[:credit.start()]

    def remove_link(match):
        trailing = re.search(r"[.,!?;:]+$", match.group(0))
        return " " + (trailing.group(0) if trailing else " ")

    text = WEB_LINK.sub(remove_link, text)
    text = re.sub(r"\(\s*Reuters\s*\)", " ", text, flags=re.I)
    text = re.sub(r"\bReuters\b", " ", text, flags=re.I)

    return re.sub(r"\s+", " ", text).strip()

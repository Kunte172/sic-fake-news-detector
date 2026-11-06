"""Claim extraction and Google Fact Check Tools integration."""

from __future__ import annotations

import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FACTCHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
MAX_CLAIMS = 3
MAX_QUERY_LENGTH = 280


def extract_claims(text: str, limit: int = MAX_CLAIMS) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    candidates = []
    for sentence in sentences:
        sentence = sentence.strip(" -")
        words = sentence.split()
        if 8 <= len(words) <= 55 and (
            re.search(
                r"\b(?:is|are|was|were|has|have|will|can|found|said|reported|according|"
                r"là|được|cho biết|theo|đã|sẽ|có thể|nghiên cứu)\b",
                sentence,
                re.I,
            )
            or re.search(r"\d", sentence)
        ):
            candidates.append(sentence[:MAX_QUERY_LENGTH])
    return candidates[:limit]


def _search_claim(query: str, api_key: str) -> list[dict]:
    params = urlencode({"query": query, "pageSize": 5, "key": api_key})
    request = Request(f"{FACTCHECK_ENDPOINT}?{params}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        payload = json.load(response)
    results = []
    for item in payload.get("claims", []):
        for review in item.get("claimReview", []):
            publisher = review.get("publisher") or {}
            results.append({
                "claim": item.get("text", query),
                "publisher": publisher.get("name"),
                "publisher_site": publisher.get("site"),
                "rating": review.get("textualRating"),
                "review_url": review.get("url"),
                "review_date": review.get("reviewDate"),
            })
    return results


def verify_claims(text: str) -> dict:
    claims = extract_claims(text)
    base = {
        "status": "INSUFFICIENT_EVIDENCE",
        "conclusion": "Chưa đủ dữ kiện",
        "claims": [{"text": claim, "reviews": []} for claim in claims],
        "sources": [],
        "limitations": [
            "Fact-check không có kết quả không chứng minh bài báo đúng.",
            "Kết luận cần đối chiếu ngày, tác giả, nguồn dẫn và nhiều nguồn độc lập.",
        ],
    }
    api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY", "").strip()
    if not api_key or not claims:
        if not api_key:
            base["limitations"].insert(0, "Chưa cấu hình GOOGLE_FACT_CHECK_API_KEY.")
        return base

    all_reviews = []
    try:
        for entry in base["claims"]:
            entry["reviews"] = _search_claim(entry["text"], api_key)
            all_reviews.extend(entry["reviews"])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        base["error"] = "Không truy cập được Google Fact Check API."
        return base

    base["sources"] = all_reviews
    ratings = " ".join((item.get("rating") or "").lower() for item in all_reviews)
    false_terms = ("false", "fake", "misleading", "pants on fire", "incorrect")
    true_terms = ("true", "correct", "accurate")
    has_false = any(term in ratings for term in false_terms)
    has_true = any(term in ratings for term in true_terms)
    if has_false and not has_true:
        base["status"] = "EVIDENCE_FALSE"
        base["conclusion"] = "Có bằng chứng bài sai"
    elif has_true and not has_false:
        base["status"] = "EVIDENCE_TRUE"
        base["conclusion"] = "Có bằng chứng bài đúng"
    return base

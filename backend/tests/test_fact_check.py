import os
import unittest
from unittest.mock import patch

from backend.app.fact_check import extract_claims, verify_claims


class FactCheckTests(unittest.TestCase):
    def test_extracts_vietnamese_claims(self):
        claims = extract_claims("Theo báo cáo, nghiên cứu này là đáng chú ý. Nghiên cứu đã phát hiện một kết quả mới trong năm 2024.")
        self.assertEqual(len(claims), 2)

    def test_without_key_is_insufficient(self):
        with patch.dict(os.environ, {}, clear=True):
            result = verify_claims("Nghiên cứu đã phát hiện một kết quả mới trong năm 2024.")
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
        self.assertIn("GOOGLE_FACT_CHECK_API_KEY", result["limitations"][0])

    def test_false_fact_check_is_contradicted_evidence(self):
        review = [{"publisher": "Example Fact Check", "rating": "False", "review_url": "https://example.test/review"}]
        with patch.dict(os.environ, {"GOOGLE_FACT_CHECK_API_KEY": "test-key"}), patch(
            "backend.app.fact_check._search_claim", return_value=review
        ):
            result = verify_claims("The study was published in 2024 and has found a new result.")
        self.assertEqual(result["status"], "EVIDENCE_FALSE")
        self.assertEqual(result["conclusion"], "Có bằng chứng bài sai")


if __name__ == "__main__":
    unittest.main()

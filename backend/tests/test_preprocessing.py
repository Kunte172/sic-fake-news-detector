import unittest

from backend.app.preprocessing import article_text, clean_text


class PreprocessingTests(unittest.TestCase):
    def test_removes_leading_reuters_dateline(self):
        self.assertEqual(clean_text("WASHINGTON (Reuters) -  A story begins here."), "A story begins here.")

    def test_preserves_body_and_normalizes_spaces(self):
        self.assertEqual(clean_text("An article\nmentions Reuters in context."), "An article mentions Reuters in context.")

    def test_joins_title_and_body(self):
        self.assertEqual(article_text("News title", "LONDON (Reuters) - Article text"), "News title Article text")


if __name__ == "__main__":
    unittest.main()

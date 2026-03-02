import unittest
from scraper import NewsItem, GoogleNewsScraper
from unittest.mock import MagicMock
import sys
# Mock spacy before importing processor
mock_spacy = MagicMock()
sys.modules["spacy"] = mock_spacy
from processor import TextSummarizer, QuestionGenerator

class TestNewsBotCore(unittest.TestCase):
    def test_news_item_creation(self):
        item = NewsItem("Title", "http://example.com", "Source")
        self.assertEqual(item.title, "Title")
        self.assertEqual(item.url, "http://example.com")

    def test_summarizer(self):
        summarizer = TextSummarizer({"max_sentences": 1})
        text = "This is a sentence. This is another sentence. This is a third one."
        summary = summarizer.process(text)
        self.assertTrue(len(summary) > 0)

    def test_question_generator(self):
        gen = QuestionGenerator({})
        text = "Apple Inc. is a technology company based in Cupertino."
        question = gen.process(text)
        self.assertTrue("Apple" in question or "?" in question)

if __name__ == "__main__":
    unittest.main()

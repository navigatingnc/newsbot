import unittest
from scraper import NewsItem
from processor import TextSummarizer, QuestionGenerator

class TestCoreModules(unittest.TestCase):
    def setUp(self):
        self.config = {"max_sentences": 2, "method": "extractive"}
        self.summarizer = TextSummarizer(self.config)
        self.q_gen = QuestionGenerator({})
        self.text = "The quick brown fox jumps over the lazy dog. It was a sunny day. Everyone was happy."

    def test_news_item_dict(self):
        item = NewsItem("Title", "http://x.com", "Source")
        d = item.to_dict()
        self.assertEqual(d["title"], "Title")
        self.assertEqual(NewsItem.from_dict(d).title, "Title")

    def test_summarization(self):
        summary = self.summarizer.process(self.text)
        self.assertTrue(len(summary) > 0)
        self.assertLessEqual(len(summary.split('. ')), 3)

    def test_question_generation(self):
        q = self.q_gen.process(self.text)
        self.assertTrue(q.endswith('?'))

if __name__ == '__main__':
    unittest.main()

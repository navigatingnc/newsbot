"""
News Bot - Content Processor Module

This module contains classes for summarizing content and generating questions:
1. Text Summarizer
2. Question Generator

Each processor is implemented as a separate class with a common interface.
"""

import re
import logging
import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from nltk.sentiment import SentimentIntensityAnalyzer

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import spacy

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentProcessor(ABC):
    """Abstract base class for content processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def process(self, text: str) -> str:
        """
        Process the input text.
        
        Args:
            text: Input text to process
            
        Returns:
            Processed text
        """
        pass


class TextSummarizer(ContentProcessor):
    """Class for summarizing text content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_sentences = config.get("max_sentences", 3)
        self.min_sentences = config.get("min_sentences", 1)
        self.method = config.get("method", "extractive")
        self.language = config.get("language", "english")
        
        # Load spaCy model for abstractive summarization if needed
        self.nlp = None
        if self.method == "abstractive":
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("SpaCy model not found. Downloading en_core_web_sm...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
    
    def process(self, text: str) -> str:
        """
        Summarize the input text.
        
        Args:
            text: Input text to summarize
            
        Returns:
            Summarized text
        """
        if not text:
            return ""
        
        if self.method == "extractive":
            return self._extractive_summarize(text)
        elif self.method == "abstractive":
            return self._abstractive_summarize(text)
        else:
            logger.warning(f"Unknown summarization method: {self.method}. Using extractive.")
            return self._extractive_summarize(text)
    
    def _extractive_summarize(self, text: str) -> str:
        """
        Perform extractive summarization using frequency-based approach.
        
        Args:
            text: Input text to summarize
            
        Returns:
            Summarized text
        """
        # Tokenize sentences
        sentences = sent_tokenize(text)
        
        # If text is already short, return it as is
        if len(sentences) <= self.min_sentences:
            return text
        
        # Tokenize words and remove stopwords
        stop_words = set(stopwords.words(self.language))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words]
        
        # Calculate word frequencies
        freq_dist = FreqDist(words)
        
        # Score sentences based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence.lower())
            sentence_words = [word for word in sentence_words if word.isalnum()]
            
            # Skip very short sentences
            if len(sentence_words) < 3:
                continue
            
            score = sum(freq_dist[word] for word in sentence_words if word in freq_dist)
            # Normalize by sentence length to avoid bias towards longer sentences
            sentence_scores[i] = score / len(sentence_words)
        
        # Select top sentences
        num_sentences = min(self.max_sentences, max(self.min_sentences, len(sentences) // 4))
        top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        
        # Arrange sentences in original order
        top_indices = sorted(top_indices)
        
        # Construct summary
        summary = " ".join(sentences[i] for i in top_indices)
        
        return summary
    
    def _abstractive_summarize(self, text: str) -> str:
        """
        Perform abstractive summarization using spaCy.
        
        This is a simplified version of abstractive summarization.
        For production use, consider using more advanced models like T5 or BART.
        
        Args:
            text: Input text to summarize
            
        Returns:
            Summarized text
        """
        if not self.nlp:
            logger.warning("SpaCy model not loaded. Falling back to extractive summarization.")
            return self._extractive_summarize(text)
        
        # Process the text with spaCy
        doc = self.nlp(text)
        
        # Extract key sentences based on entity recognition
        sentences = list(doc.sents)
        
        if len(sentences) <= self.min_sentences:
            return text
        
        # Score sentences based on named entities and noun chunks
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            # Count entities in the sentence
            entity_count = len([ent for ent in doc.ents if ent.start >= sentence.start and ent.end <= sentence.end])
            
            # Count noun chunks in the sentence
            chunk_count = len([chunk for chunk in doc.noun_chunks if chunk.start >= sentence.start and chunk.end <= sentence.end])
            
            # Score based on entities and chunks, normalized by sentence length
            score = (entity_count + chunk_count) / len(sentence)
            sentence_scores[i] = score
        
        # Select top sentences
        num_sentences = min(self.max_sentences, max(self.min_sentences, len(sentences) // 4))
        top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
        
        # Arrange sentences in original order
        top_indices = sorted(top_indices)
        
        # Construct summary
        summary = " ".join(str(sentences[i]) for i in top_indices)
        
        return summary


class QuestionGenerator(ContentProcessor):
    """Class for generating questions based on content."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.question_types = config.get("question_types", ["what", "why", "how"])
        self.language = config.get("language", "english")
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found. Downloading en_core_web_sm...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
    
    def process(self, text: str) -> str:
        """
        Generate a question based on the input text.
        
        Args:
            text: Input text to generate question from
            
        Returns:
            Generated question
        """
        if not text:
            return ""
        
        # Try different methods to generate a question
        question = self._generate_entity_question(text)
        
        if not question:
            question = self._generate_template_question(text)
        
        return question
    
    def _generate_entity_question(self, text: str) -> str:
        """
        Generate a question based on entities in the text.
        
        Args:
            text: Input text
            
        Returns:
            Generated question or empty string if no suitable entities found
        """
        doc = self.nlp(text)
        
        # Extract entities
        entities = list(doc.ents)
        if not entities:
            return ""
        
        # Filter for interesting entity types
        interesting_types = ["PERSON", "ORG", "GPE", "EVENT", "PRODUCT", "WORK_OF_ART"]
        interesting_entities = [ent for ent in entities if ent.label_ in interesting_types]
        
        if not interesting_entities:
            interesting_entities = entities  # Fallback to all entities
        
        # Select a random entity
        entity = random.choice(interesting_entities)
        
        # Generate question based on entity type
        if entity.label_ == "PERSON":
            templates = [
                f"What role did {entity.text} play in this situation?",
                f"Why is {entity.text} significant in this context?",
                f"How might {entity.text}'s actions impact future developments?"
            ]
        elif entity.label_ == "ORG":
            templates = [
                f"What are the implications of {entity.text}'s involvement?",
                f"How might {entity.text}'s position evolve in the future?",
                f"Why is {entity.text}'s role important in this context?"
            ]
        elif entity.label_ == "GPE":  # Geopolitical entity (countries, cities)
            templates = [
                f"How might these developments affect {entity.text}?",
                f"What are the broader implications for {entity.text}?",
                f"Why is {entity.text} significant in this situation?"
            ]
        elif entity.label_ == "EVENT":
            templates = [
                f"What might be the long-term consequences of {entity.text}?",
                f"How could {entity.text} shape future developments?",
                f"Why is {entity.text} considered significant?"
            ]
        else:
            templates = [
                f"What makes {entity.text} significant in this context?",
                f"How might {entity.text} influence future developments?",
                f"Why is {entity.text} important to consider?"
            ]
        
        return random.choice(templates)
    
    def _generate_template_question(self, text: str) -> str:
        """
        Generate a question using templates when entity-based generation fails.
        
        Args:
            text: Input text
            
        Returns:
            Generated question
        """
        # Extract key nouns and verbs for context
        doc = self.nlp(text)
        
        # Get main nouns
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        if not nouns:
            # Fallback to generic questions
            return self._generate_generic_question()
        
        main_noun = random.choice(nouns)
        
        # Template questions based on question type
        question_type = random.choice(self.question_types)
        
        if question_type == "what":
            templates = [
                f"What are the broader implications of this {main_noun}?",
                f"What might be the next developments in this {main_noun}?",
                f"What do you think about this {main_noun}?"
            ]
        elif question_type == "why":
            templates = [
                f"Why is this {main_noun} significant?",
                f"Why might this {main_noun} matter in the long run?",
                f"Why should we pay attention to this {main_noun}?"
            ]
        elif question_type == "how":
            templates = [
                f"How might this {main_noun} affect future developments?",
                f"How could this {main_noun} change our understanding?",
                f"How do you see this {main_noun} evolving?"
            ]
        else:
            templates = [
                f"Do you think this {main_noun} will have lasting impact?",
                f"Is this {main_noun} as important as it seems?",
                f"Could this {main_noun} lead to significant changes?"
            ]
        
        return random.choice(templates)
    
    def _generate_generic_question(self) -> str:
        """
        Generate a generic question when other methods fail.
        
        Returns:
            Generic question
        """
        generic_questions = [
            "What do you think about this development?",
            "How might this news impact the broader context?",
            "Why is this news significant?",
            "What could be the long-term implications?",
            "How might this situation evolve in the future?",
            "Do you see this as a positive or negative development?",
            "What other factors might be influencing this situation?",
            "How does this compare to similar situations in the past?",
            "What questions does this raise for you?",
            "What might be missing from this story?"
        ]
        
        return random.choice(generic_questions)


class ContentProcessorFactory:
    """Factory for creating content processors."""
    
    @staticmethod
    def create_processor(processor_type: str, config: Dict[str, Any]) -> ContentProcessor:
        """
        Create a content processor based on the type.
        
        Args:
            processor_type: Type of processor to create (summarizer, question_generator)
            config: Configuration for the processor
            
        Returns:
            ContentProcessor instance
        """
        if processor_type == "summarizer":
            return TextSummarizer(config)
        elif processor_type == "question_generator":
            return QuestionGenerator(config)
        else:
            raise ValueError(f"Unknown processor type: {processor_type}")


class ContentProcessorManager:
    """Manager for coordinating content processing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.sia = SentimentIntensityAnalyzer()
        if config is None:
            config = {}
        self.config = config
            
        # Create summarizer
        summarizer_config = config.get("summarizer", {
            "max_sentences": 3,
            "min_sentences": 1,
            "method": "extractive",
            "language": "english"
        })
        self.summarizer = TextSummarizer(summarizer_config)
        
        # Create question generator
        question_generator_config = config.get("question_generator", {
            "question_types": ["what", "why", "how"],
            "language": "english"
        })
        self.question_generator = QuestionGenerator(question_generator_config)
    
    def process_news_item(self, news_item):
        """
        Process a news item by summarizing content and generating a question.
        
        Args:
            news_item: NewsItem object to process
            
        Returns:
            Processed NewsItem
        """
        text = news_item.content or news_item.summary or news_item.title
        sentiment = self.sia.polarity_scores(text)
        news_item.sentiment = sentiment
        if sentiment['compound'] < self.config.get("sentiment_threshold", -0.5):
            logger.info(f"Skipping negative news: {news_item.title} ({sentiment['compound']})")
            return None

        # Use existing summary if available, otherwise generate from content
        if not news_item.summary and news_item.content:
            news_item.summary = self.summarizer.process(news_item.content)
        elif not news_item.summary:
            news_item.summary = news_item.title
        
        # Generate a question based on the summary or content
        text_for_question = news_item.summary if news_item.summary else news_item.content
        if not text_for_question:
            text_for_question = news_item.title
            
        news_item.question = self.question_generator.process(text_for_question)
        
        # Mark as processed
        news_item.processed = True
        
        return news_item
    
    def process_news_items(self, news_items):
        """
        Process multiple news items.
        
        Args:
            news_items: List of NewsItem objects
            
        Returns:
            List of processed NewsItem objects
        """
        processed_items = []
        
        for item in news_items:
            try:
                processed_item = self.process_news_item(item)
                if processed_item:
                    processed_items.append(processed_item)
            except Exception as e:
                logger.error(f"Error processing news item: {e}")
                processed_items.append(item)
        
        return processed_items


# Example usage
if __name__ == "__main__":
    # Sample news item (mock)
    class MockNewsItem:
        def __init__(self, title, content):
            self.title = title
            self.content = content
            self.summary = ""
            self.question = ""
            self.processed = False
    
    # Create a sample news item
    sample_news = MockNewsItem(
        "Climate Change Accelerates Melting of Arctic Ice",
        """
        Scientists have observed an alarming acceleration in the melting of Arctic ice caps over the past decade.
        According to a new study published in the journal Nature, the rate of ice loss has increased by 65% since 2010.
        The research team, led by Dr. Sarah Johnson of the Polar Research Institute, used satellite data and on-site measurements to track changes in ice thickness and coverage.
        "What we're seeing is unprecedented in the historical record," said Dr. Johnson. "The rate of change is much faster than our climate models predicted."
        The study found that summer ice coverage has decreased by nearly 30% compared to the 1979-2000 average.
        This rapid melting is expected to have significant impacts on global weather patterns, sea levels, and wildlife habitats.
        Arctic species like polar bears are already struggling to adapt to the changing conditions.
        The researchers also noted that the melting ice creates a feedback loop, as darker ocean water absorbs more heat than reflective ice, further accelerating warming.
        World leaders are being urged to take immediate action to reduce carbon emissions in light of these findings.
        "This isn't just about saving the Arctic," Dr. Johnson emphasized. "It's about preventing catastrophic changes to the climate system that supports all life on Earth."
        """
    )
    
    # Create a content processor manager
    processor_manager = ContentProcessorManager()
    
    # Process the news item
    processed_news = processor_manager.process_news_item(sample_news)
    
    # Print results
    print(f"Title: {processed_news.title}")
    print(f"Summary: {processed_news.summary}")
    print(f"Question: {processed_news.question}")

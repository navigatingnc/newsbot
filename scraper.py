"""
News Bot - Scraper Module

This module contains classes for scraping news from various sources:
1. Google Search
2. Website Scraping
3. RSS Feeds

Each scraper is implemented as a separate class with a common interface.
"""

import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsItem:
    """Class representing a news item with standardized fields."""
    
    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        published_date: Optional[datetime] = None,
        content: str = "",
        summary: str = "",
        image_url: str = ""
    ):
        self.title = title
        self.url = url
        self.source = source
        self.published_date = published_date or datetime.now()
        self.content = content
        self.summary = summary
        self.image_url = image_url
        self.processed = False
        self.question = ""
        self.generated_image_path = ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the news item to a dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_date": self.published_date.isoformat(),
            "content": self.content,
            "summary": self.summary,
            "image_url": self.image_url,
            "processed": self.processed,
            "question": self.question,
            "generated_image_path": self.generated_image_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsItem':
        """Create a NewsItem from a dictionary."""
        item = cls(
            title=data["title"],
            url=data["url"],
            source=data["source"],
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            image_url=data.get("image_url", "")
        )
        
        if "published_date" in data:
            try:
                item.published_date = datetime.fromisoformat(data["published_date"])
            except (ValueError, TypeError):
                item.published_date = datetime.now()
                
        item.processed = data.get("processed", False)
        item.question = data.get("question", "")
        item.generated_image_path = data.get("generated_image_path", "")
        
        return item


class NewsScraper(ABC):
    """Abstract base class for news scrapers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_agent = config.get("user_agent", "NewsBot/1.0")
        self.headers = {
            "User-Agent": self.user_agent
        }
    
    @abstractmethod
    def scrape(self, topic: str, max_results: int = 10) -> List[NewsItem]:
        """
        Scrape news for a given topic.
        
        Args:
            topic: The topic to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of NewsItem objects
        """
        pass
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content by removing tags and extra whitespace."""
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ")
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_main_image(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract the main image URL from a BeautifulSoup object."""
        # Try to find meta og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return urljoin(base_url, og_image["content"])
        
        # Try to find the first large image
        for img in soup.find_all("img", src=True):
            if img.get("width") and int(img["width"]) > 300:
                return urljoin(base_url, img["src"])
            if img.get("height") and int(img["height"]) > 200:
                return urljoin(base_url, img["src"])
            # Check if image has class containing "featured" or "main"
            img_class = img.get("class", [])
            if any(c for c in img_class if "featured" in c.lower() or "main" in c.lower()):
                return urljoin(base_url, img["src"])
        
        # Fallback to first image
        first_img = soup.find("img", src=True)
        if first_img:
            return urljoin(base_url, first_img["src"])
        
        return ""


class GoogleNewsScraper(NewsScraper):
    """Scraper for Google News."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.search_url = "https://www.google.com/search"
        self.time_period = config.get("time_period", "1d")  # Default to 1 day
    
    def scrape(self, topic: str, max_results: int = 10) -> List[NewsItem]:
        """Scrape news from Google for a given topic."""
        logger.info(f"Scraping Google News for topic: {topic}")
        
        # Prepare search parameters
        params = {
            "q": f"{topic} news",
            "tbm": "nws",  # News search
            "tbs": f"qdr:{self.time_period}"  # Time period
        }
        
        try:
            response = requests.get(self.search_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            news_items = []
            
            # Extract news items from Google search results
            for result in soup.select("div.SoaBEf")[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.select_one("div.mCBkyc")
                    link_elem = result.select_one("a")
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    url = link_elem.get("href", "")
                    
                    # Clean URL (Google prepends with /url?q=)
                    if url.startswith("/url?q="):
                        url = url.split("/url?q=")[1].split("&")[0]
                    
                    # Extract source
                    source_elem = result.select_one("div.CEMjEf")
                    source = source_elem.text.strip() if source_elem else "Unknown"
                    
                    # Extract date if available
                    date_elem = result.select_one("div.OSrXXb span")
                    published_date = datetime.now()
                    if date_elem:
                        date_text = date_elem.text.strip()
                        # Parse relative dates like "2 hours ago", "1 day ago"
                        if "hour" in date_text:
                            hours = int(re.search(r'(\d+)', date_text).group(1))
                            published_date = datetime.now() - timedelta(hours=hours)
                        elif "day" in date_text:
                            days = int(re.search(r'(\d+)', date_text).group(1))
                            published_date = datetime.now() - timedelta(days=days)
                        elif "minute" in date_text:
                            minutes = int(re.search(r'(\d+)', date_text).group(1))
                            published_date = datetime.now() - timedelta(minutes=minutes)
                    
                    # Extract snippet/summary
                    snippet_elem = result.select_one("div.GI74Re")
                    summary = snippet_elem.text.strip() if snippet_elem else ""
                    
                    # Create NewsItem
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source=source,
                        published_date=published_date,
                        summary=summary
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.error(f"Error parsing Google News result: {e}")
                    continue
            
            logger.info(f"Found {len(news_items)} news items from Google News")
            return news_items
            
        except Exception as e:
            logger.error(f"Error scraping Google News: {e}")
            return []


class WebsiteScraper(NewsScraper):
    """Scraper for general websites."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sites = config.get("sites", [])
        self.max_depth = config.get("max_depth", 1)
        self.timeout = config.get("timeout", 10)
    
    def scrape(self, topic: str, max_results: int = 10) -> List[NewsItem]:
        """Scrape news from configured websites for a given topic."""
        logger.info(f"Scraping websites for topic: {topic}")
        
        news_items = []
        
        for site in self.sites:
            try:
                site_url = site.get("url")
                if not site_url:
                    continue
                
                logger.info(f"Scraping website: {site_url}")
                
                # Get the main page
                response = requests.get(
                    site_url, 
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract links based on site-specific selectors or default approach
                article_selector = site.get("article_selector", "a")
                links = soup.select(article_selector)
                
                # Filter links that might be related to the topic
                topic_keywords = topic.lower().split()
                relevant_links = []
                
                for link in links:
                    href = link.get("href")
                    if not href:
                        continue
                    
                    # Make URL absolute
                    if not href.startswith(("http://", "https://")):
                        href = urljoin(site_url, href)
                    
                    # Skip non-article URLs (e.g., login, about pages)
                    if any(skip in href.lower() for skip in [
                        "login", "signin", "register", "about", "contact", 
                        "terms", "privacy", "advertise"
                    ]):
                        continue
                    
                    # Check if link text or URL contains topic keywords
                    link_text = link.text.lower()
                    if any(keyword in link_text or keyword in href.lower() for keyword in topic_keywords):
                        relevant_links.append(href)
                
                # Limit the number of links to process
                relevant_links = relevant_links[:max_results]
                
                # Process each relevant link
                for url in relevant_links:
                    try:
                        article = self._scrape_article(url, site)
                        if article:
                            news_items.append(article)
                            
                            # Break if we've reached max_results
                            if len(news_items) >= max_results:
                                break
                    except Exception as e:
                        logger.error(f"Error scraping article {url}: {e}")
                        continue
                
                # Break if we've reached max_results
                if len(news_items) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping website {site.get('url')}: {e}")
                continue
        
        logger.info(f"Found {len(news_items)} news items from websites")
        return news_items
    
    def _scrape_article(self, url: str, site_config: Dict[str, Any]) -> Optional[NewsItem]:
        """Scrape a single article from a URL."""
        try:
            response = requests.get(
                url, 
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title
            title_selector = site_config.get("title_selector", "h1")
            title_elem = soup.select_one(title_selector)
            title = title_elem.text.strip() if title_elem else ""
            
            if not title:
                # Try common title elements
                for selector in ["h1", "h1.title", "h1.article-title", "title"]:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = title_elem.text.strip()
                        break
            
            # Extract content
            content_selector = site_config.get("content_selector", "article")
            content_elem = soup.select_one(content_selector)
            
            if not content_elem:
                # Try common content elements
                for selector in ["article", "div.article", "div.content", "div.article-content"]:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        break
            
            content = ""
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select("script, style, nav, footer, .comments, .related"):
                    unwanted.decompose()
                
                content = content_elem.get_text(separator=" ").strip()
                content = re.sub(r'\s+', ' ', content)
            
            # Extract published date
            date_selector = site_config.get("date_selector", "time")
            date_elem = soup.select_one(date_selector)
            
            published_date = datetime.now()
            if date_elem:
                date_str = date_elem.get("datetime") or date_elem.text.strip()
                try:
                    # Try various date formats
                    for date_format in [
                        "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
                        "%Y-%m-%dT%H:%M:%S",    # ISO format without timezone
                        "%Y-%m-%d %H:%M:%S",    # Common format
                        "%B %d, %Y",            # Month name, day, year
                        "%d %B %Y",             # Day, month name, year
                        "%m/%d/%Y",             # US format
                        "%d/%m/%Y",             # European format
                    ]:
                        try:
                            published_date = datetime.strptime(date_str, date_format)
                            break
                        except ValueError:
                            continue
                except Exception:
                    # Keep default date if parsing fails
                    pass
            
            # Extract image
            image_url = self._extract_main_image(soup, url)
            
            # Create a summary (first few sentences)
            summary = ""
            if content:
                sentences = re.split(r'(?<=[.!?])\s+', content)
                summary = " ".join(sentences[:3])
            
            # Create NewsItem
            source = urlparse(url).netloc
            
            return NewsItem(
                title=title,
                url=url,
                source=source,
                published_date=published_date,
                content=content,
                summary=summary,
                image_url=image_url
            )
            
        except Exception as e:
            logger.error(f"Error in _scrape_article for {url}: {e}")
            return None


class RSSFeedScraper(NewsScraper):
    """Scraper for RSS feeds."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.feeds = config.get("feeds", [])
        self.max_age_days = config.get("max_age_days", 1)
    
    def scrape(self, topic: str, max_results: int = 10) -> List[NewsItem]:
        """Scrape news from RSS feeds for a given topic."""
        logger.info(f"Scraping RSS feeds for topic: {topic}")
        
        news_items = []
        topic_keywords = topic.lower().split()
        
        for feed_url in self.feeds:
            try:
                logger.info(f"Parsing RSS feed: {feed_url}")
                
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    try:
                        # Check if entry is related to the topic
                        title = entry.get("title", "").lower()
                        description = entry.get("description", "").lower()
                        
                        if not any(keyword in title or keyword in description for keyword in topic_keywords):
                            continue
                        
                        # Extract URL
                        url = entry.get("link", "")
                        if not url:
                            continue
                        
                        # Extract published date
                        published_date = datetime.now()
                        if "published_parsed" in entry:
                            published_date = datetime(*entry.published_parsed[:6])
                        elif "updated_parsed" in entry:
                            published_date = datetime(*entry.updated_parsed[:6])
                        
                        # Skip if too old
                        age_days = (datetime.now() - published_date).days
                        if age_days > self.max_age_days:
                            continue
                        
                        # Extract content
                        content = ""
                        if "content" in entry:
                            content = entry.content[0].value
                        elif "summary" in entry:
                            content = entry.summary
                        
                        # Clean content
                        if content:
                            content = self._clean_html(content)
                        
                        # Extract source
                        source = feed.feed.get("title", urlparse(feed_url).netloc)
                        
                        # Create summary
                        summary = description if "description" in entry else ""
                        if not summary and content:
                            sentences = re.split(r'(?<=[.!?])\s+', content)
                            summary = " ".join(sentences[:3])
                        
                        # Extract image URL
                        image_url = ""
                        if "media_content" in entry:
                            for media in entry.media_content:
                                if media.get("medium") == "image":
                                    image_url = media.get("url", "")
                                    break
                        
                        if not image_url and "links" in entry:
                            for link in entry.links:
                                if link.get("type", "").startswith("image/"):
                                    image_url = link.get("href", "")
                                    break
                        
                        # Create NewsItem
                        news_item = NewsItem(
                            title=entry.get("title", ""),
                            url=url,
                            source=source,
                            published_date=published_date,
                            content=content,
                            summary=summary,
                            image_url=image_url
                        )
                        
                        news_items.append(news_item)
                        
                        # Break if we've reached max_results
                        if len(news_items) >= max_results:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error parsing RSS entry: {e}")
                        continue
                
                # Break if we've reached max_results
                if len(news_items) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {e}")
                continue
        
        logger.info(f"Found {len(news_items)} news items from RSS feeds")
        return news_items


class NewsScraperFactory:
    """Factory for creating news scrapers."""
    
    @staticmethod
    def create_scraper(scraper_type: str, config: Dict[str, Any]) -> NewsScraper:
        """
        Create a news scraper based on the type.
        
        Args:
            scraper_type: Type of scraper to create (google, website, rss)
            config: Configuration for the scraper
            
        Returns:
            NewsScraper instance
        """
        if scraper_type == "google":
            return GoogleNewsScraper(config)
        elif scraper_type == "website":
            return WebsiteScraper(config)
        elif scraper_type == "rss":
            return RSSFeedScraper(config)
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")


class NewsScraperManager:
    """Manager for coordinating multiple news scrapers."""
    
    def __init__(self, config_path: str = None):
        self.scrapers = []
        self.config = {}
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Initialize scrapers from config
            self._init_scrapers_from_config()
        else:
            # Use default configuration
            self._init_default_scrapers()
    
    def _init_scrapers_from_config(self):
        """Initialize scrapers from configuration file."""
        for scraper_config in self.config.get("scrapers", []):
            scraper_type = scraper_config.get("type")
            if not scraper_type:
                continue
                
            try:
                scraper = NewsScraperFactory.create_scraper(
                    scraper_type, 
                    scraper_config.get("config", {})
                )
                self.scrapers.append(scraper)
            except Exception as e:
                logger.error(f"Error creating scraper {scraper_type}: {e}")
    
    def _init_default_scrapers(self):
        """Initialize default scrapers."""
        # Google News scraper
        google_config = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "time_period": "1d"
        }
        self.scrapers.append(GoogleNewsScraper(google_config))
        
        # Website scraper with some common news sites
        website_config = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "sites": [
                {
                    "url": "https://www.bbc.com/news",
                    "title_selector": "h1",
                    "content_selector": "article",
                    "date_selector": "time"
                },
                {
                    "url": "https://www.cnn.com",
                    "title_selector": "h1.pg-headline",
                    "content_selector": "div.article__content",
                    "date_selector": "div.timestamp"
                },
                {
                    "url": "https://www.reuters.com",
                    "title_selector": "h1",
                    "content_selector": "div.article-body",
                    "date_selector": "time"
                }
            ],
            "timeout": 10
        }
        self.scrapers.append(WebsiteScraper(website_config))
        
        # RSS feed scraper with some common news feeds
        rss_config = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "feeds": [
                "http://rss.cnn.com/rss/cnn_topstories.rss",
                "http://feeds.bbci.co.uk/news/rss.xml",
                "https://www.reddit.com/r/news/.rss",
                "https://news.google.com/rss"
            ],
            "max_age_days": 1
        }
        self.scrapers.append(RSSFeedScraper(rss_config))
    
    def scrape_news(self, topic: str, max_results_per_scraper: int = 5) -> List[NewsItem]:
        """
        Scrape news from all configured scrapers.
        
        Args:
            topic: Topic to search for
            max_results_per_scraper: Maximum results to get from each scraper
            
        Returns:
            List of NewsItem objects
        """
        all_news_items = []
        
        for scraper in self.scrapers:
            try:
                news_items = scraper.scrape(topic, max_results_per_scraper)
                all_news_items.extend(news_items)
            except Exception as e:
                logger.error(f"Error with scraper {type(scraper).__name__}: {e}")
        
        # Remove duplicates based on URL
        unique_urls = set()
        unique_news_items = []
        
        for item in all_news_items:
            if item.url not in unique_urls:
                unique_urls.add(item.url)
                unique_news_items.append(item)
        
        # Sort by published date (newest first)
        unique_news_items.sort(key=lambda x: x.published_date, reverse=True)
        
        return unique_news_items
    
    def save_news_items(self, news_items: List[NewsItem], output_file: str):
        """
        Save news items to a JSON file.
        
        Args:
            news_items: List of NewsItem objects
            output_file: Path to output file
        """
        data = [item.to_dict() for item in news_items]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(news_items)} news items to {output_file}")
    
    def load_news_items(self, input_file: str) -> List[NewsItem]:
        """
        Load news items from a JSON file.
        
        Args:
            input_file: Path to input file
            
        Returns:
            List of NewsItem objects
        """
        if not os.path.exists(input_file):
            logger.warning(f"Input file {input_file} does not exist")
            return []
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        news_items = [NewsItem.from_dict(item) for item in data]
        logger.info(f"Loaded {len(news_items)} news items from {input_file}")
        
        return news_items


# Example usage
if __name__ == "__main__":
    # Create a scraper manager
    manager = NewsScraperManager()
    
    # Scrape news for a topic
    news_items = manager.scrape_news("climate change", max_results_per_scraper=3)
    
    # Print results
    for item in news_items:
        print(f"Title: {item.title}")
        print(f"Source: {item.source}")
        print(f"URL: {item.url}")
        print(f"Date: {item.published_date}")
        print(f"Summary: {item.summary[:100]}...")
        print("-" * 50)
    
    # Save to file
    manager.save_news_items(news_items, "climate_news.json")

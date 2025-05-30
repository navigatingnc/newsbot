"""
News Bot - Main Module

This module integrates all components of the News Bot:
1. News Scraper
2. Content Processor
3. Image Generator
4. Social Media Poster
5. Main Bot Controller
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Import modules
from scraper import NewsScraperManager, NewsItem
from processor import ContentProcessorManager
from image_generator import ImageManager
from poster import SocialMediaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("news_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NewsBot:
    """Main class for the News Bot."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the News Bot.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = {}
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Use default configuration
            self.config = {
                "output_dir": "output",
                "scraper": {
                    "max_results_per_source": 3
                },
                "processor": {
                    "summarizer": {
                        "max_sentences": 3,
                        "method": "extractive"
                    },
                    "question_generator": {
                        "question_types": ["what", "why", "how"]
                    }
                },
                "image_generator": {
                    "generator_type": "simple",
                    "generator_config": {
                        "output_dir": "images",
                        "width": 1200,
                        "height": 630
                    }
                },
                "poster": {
                    "platforms": {}
                }
            }
        
        # Create output directory
        os.makedirs(self.config.get("output_dir", "output"), exist_ok=True)
        
        # Initialize components
        self.scraper_manager = NewsScraperManager()
        self.processor_manager = ContentProcessorManager(self.config.get("processor", {}))
        self.image_manager = ImageManager(self.config.get("image_generator", {}))
        self.poster_manager = SocialMediaManager()
        
        # Initialize platforms from config
        for platform, platform_config in self.config.get("poster", {}).get("platforms", {}).items():
            if platform_config.get("enabled", False):
                self.poster_manager.add_poster(platform, platform_config)
    
    def run(self, topic: str) -> List[Dict[str, Any]]:
        """
        Run the complete news bot pipeline for a topic.
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of posting results
        """
        logger.info(f"Starting news bot pipeline for topic: {topic}")
        
        # Step 1: Scrape news
        max_results = self.config.get("scraper", {}).get("max_results_per_source", 3)
        news_items = self.scraper_manager.scrape_news(topic, max_results)
        
        if not news_items:
            logger.warning(f"No news found for topic: {topic}")
            return []
        
        logger.info(f"Found {len(news_items)} news items for topic: {topic}")
        
        # Save raw news items
        output_dir = self.config.get("output_dir", "output")
        raw_output_file = os.path.join(output_dir, f"{topic.replace(' ', '_')}_raw.json")
        self.scraper_manager.save_news_items(news_items, raw_output_file)
        
        # Step 2: Process content (summarize and generate questions)
        processed_items = self.processor_manager.process_news_items(news_items)
        
        # Save processed items
        processed_output_file = os.path.join(output_dir, f"{topic.replace(' ', '_')}_processed.json")
        self.scraper_manager.save_news_items(processed_items, processed_output_file)
        
        # Step 3: Generate images
        items_with_images = self.image_manager.generate_images_for_news_items(processed_items)
        
        # Save items with images
        images_output_file = os.path.join(output_dir, f"{topic.replace(' ', '_')}_with_images.json")
        self.scraper_manager.save_news_items(items_with_images, images_output_file)
        
        # Step 4: Post to social media
        all_posting_results = []
        
        for item in items_with_images:
            # Post to all platforms
            posting_results = self.poster_manager.post_to_all_platforms(item)
            all_posting_results.append({
                "news_item": item.to_dict(),
                "posting_results": posting_results
            })
            
            # Save posting results
            posting_output_file = os.path.join(output_dir, f"{topic.replace(' ', '_')}_posting_results.json")
            self.poster_manager.save_posting_results(item, posting_results, posting_output_file)
        
        logger.info(f"Completed news bot pipeline for topic: {topic}")
        return all_posting_results
    
    def add_platform(self, platform: str, config: Dict[str, Any]):
        """
        Add a social media platform.
        
        Args:
            platform: Platform name (twitter, reddit, forum, instagram)
            config: Platform configuration
        """
        self.poster_manager.add_poster(platform, config)
        
        # Update config
        if "poster" not in self.config:
            self.config["poster"] = {"platforms": {}}
        if "platforms" not in self.config["poster"]:
            self.config["poster"]["platforms"] = {}
            
        self.config["poster"]["platforms"][platform] = config
    
    def save_config(self, config_path: str):
        """
        Save the current configuration to a file.
        
        Args:
            config_path: Path to save configuration
        """
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")


def main():
    """Main entry point for the News Bot CLI."""
    parser = argparse.ArgumentParser(description="News Bot - Scrape, summarize, and post news")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--topic", help="Topic to search for")
    
    args = parser.parse_args()
    
    if not args.topic:
        print("Error: Topic is required")
        parser.print_help()
        return
    
    # Initialize the bot
    bot = NewsBot(args.config)
    
    # Run the bot
    results = bot.run(args.topic)
    
    # Print results
    for result in results:
        news_item = result["news_item"]
        print(f"Title: {news_item['title']}")
        print(f"Summary: {news_item['summary']}")
        print(f"Question: {news_item['question']}")
        print(f"Image: {news_item['generated_image_path']}")
        print("Posting Results:")
        
        for posting in result["posting_results"]:
            platform = posting.get("platform", "Unknown")
            success = posting.get("success", False)
            message = posting.get("message", "")
            url = posting.get("url", "")
            
            status = "Success" if success else "Failed"
            print(f"  {platform}: {status}")
            if url:
                print(f"    URL: {url}")
            if message and not success:
                print(f"    Error: {message}")
        
        print("-" * 50)


if __name__ == "__main__":
    main()

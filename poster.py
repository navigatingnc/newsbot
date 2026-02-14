"""
News Bot - Social Media Poster Module

This module contains classes for posting to various social media platforms:
1. X (Twitter) Poster
2. Reddit Poster
3. Self-hosted Forum Poster
4. Instagram Poster
5. Social Media Manager
"""

import os
import logging
import json
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
import tweepy
import praw
from instagrapi import Client as InstagrapiClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SocialMediaPoster(ABC):
    """Abstract base class for social media posters."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = "Unknown"
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def post(self, title: str, content: str, image_path: str = "", url: str = "") -> Dict[str, Any]:
        """
        Post content to the platform.
        
        Args:
            title: Title of the post
            content: Main content of the post
            image_path: Optional path to an image to include
            url: Optional URL to include
            
        Returns:
            Dictionary with post status and details
        """
        pass
    
    def format_content(self, title: str, content: str, question: str = "", url: str = "") -> str:
        """
        Format content for the platform.
        
        Args:
            title: Title of the post
            content: Main content of the post
            question: Optional question to include
            url: Optional URL to include
            
        Returns:
            Formatted content string
        """
        # Default implementation - override in subclasses
        formatted = f"{title}\n\n{content}"
        
        if question:
            formatted += f"\n\n{question}"
            
        if url:
            formatted += f"\n\n{url}"
            
        return formatted


class TwitterPoster(SocialMediaPoster):
    """Poster for X (Twitter)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "X (Twitter)"
        self.api = None
        self.max_length = 280  # X character limit
        
        # Required credentials
        self.consumer_key = config.get("consumer_key", "")
        self.consumer_secret = config.get("consumer_secret", "")
        self.access_token = config.get("access_token", "")
        self.access_token_secret = config.get("access_token_secret", "")
    
    def authenticate(self) -> bool:
        """Authenticate with X (Twitter)."""
        if not all([self.consumer_key, self.consumer_secret, 
                   self.access_token, self.access_token_secret]):
            logger.error("Missing Twitter API credentials")
            return False
        
        try:
            # Initialize the API
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key, 
                self.consumer_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api = tweepy.API(auth)
            
            # Verify credentials
            self.api.verify_credentials()
            logger.info("Twitter authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False
    
    def format_content(self, title: str, content: str, question: str = "", url: str = "") -> str:
        """Format content for Twitter."""
        # Calculate available space
        url_length = len(url) + 1 if url else 0
        question_length = len(question) + 2 if question else 0
        available_length = self.max_length - url_length - question_length
        
        # Combine title and content
        combined = f"{title}: {content}"
        
        # Truncate if needed
        if len(combined) > available_length:
            combined = combined[:available_length-3] + "..."
        
        # Add question and URL
        if question:
            combined += f"\n\n{question}"
            
        if url:
            combined += f"\n{url}"
            
        return combined
    
    def post(self, title: str, content: str, image_path: str = "", url: str = "") -> Dict[str, Any]:
        """Post to X (Twitter)."""
        if not self.api:
            if not self.authenticate():
                return {"success": False, "message": "Authentication failed"}
        
        try:
            # Format the content
            formatted_content = self.format_content(title, content, "", url)
            
            # Post with or without media
            if image_path and os.path.exists(image_path):
                # Upload media
                media = self.api.media_upload(image_path)
                media_id = media.media_id_string
                
                # Post with media
                status = self.api.update_status(
                    status=formatted_content,
                    media_ids=[media_id]
                )
                
                logger.info(f"Posted to Twitter with image: {status.id}")
                return {
                    "success": True,
                    "post_id": status.id,
                    "url": f"https://twitter.com/user/status/{status.id}"
                }
            else:
                # Post text only
                status = self.api.update_status(formatted_content)
                
                logger.info(f"Posted to Twitter: {status.id}")
                return {
                    "success": True,
                    "post_id": status.id,
                    "url": f"https://twitter.com/user/status/{status.id}"
                }
                
        except Exception as e:
            logger.error(f"Error posting to Twitter: {e}")
            return {"success": False, "message": str(e)}


class RedditPoster(SocialMediaPoster):
    """Poster for Reddit."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "Reddit"
        self.reddit = None
        
        # Required credentials
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.user_agent = config.get("user_agent", "NewsBot/1.0")
        
        # Subreddit to post to
        self.subreddit = config.get("subreddit", "")
    
    def authenticate(self) -> bool:
        """Authenticate with Reddit."""
        if not all([self.client_id, self.client_secret, 
                   self.username, self.password, self.user_agent]):
            logger.error("Missing Reddit API credentials")
            return False
        
        try:
            # Initialize the Reddit instance
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
            
            # Verify authentication
            username = self.reddit.user.me().name
            logger.info(f"Reddit authentication successful as {username}")
            return True
            
        except Exception as e:
            logger.error(f"Reddit authentication failed: {e}")
            return False
    
    def post(self, title: str, content: str, image_path: str = "", url: str = "") -> Dict[str, Any]:
        """Post to Reddit."""
        if not self.reddit:
            if not self.authenticate():
                return {"success": False, "message": "Authentication failed"}
        
        if not self.subreddit:
            return {"success": False, "message": "No subreddit specified"}
        
        try:
            subreddit = self.reddit.subreddit(self.subreddit)
            
            # Determine post type
            if url:
                # Link post
                submission = subreddit.submit(
                    title=title,
                    url=url
                )
                
                # Add a comment with the content
                if content:
                    submission.reply(content)
                
                logger.info(f"Posted link to Reddit: {submission.id}")
                return {
                    "success": True,
                    "post_id": submission.id,
                    "url": f"https://www.reddit.com{submission.permalink}"
                }
                
            elif image_path and os.path.exists(image_path):
                # Image post
                submission = subreddit.submit_image(
                    title=title,
                    image_path=image_path
                )
                
                # Add a comment with the content
                if content:
                    submission.reply(content)
                
                logger.info(f"Posted image to Reddit: {submission.id}")
                return {
                    "success": True,
                    "post_id": submission.id,
                    "url": f"https://www.reddit.com{submission.permalink}"
                }
                
            else:
                # Text post
                submission = subreddit.submit(
                    title=title,
                    selftext=content
                )
                
                logger.info(f"Posted text to Reddit: {submission.id}")
                return {
                    "success": True,
                    "post_id": submission.id,
                    "url": f"https://www.reddit.com{submission.permalink}"
                }
                
        except Exception as e:
            logger.error(f"Error posting to Reddit: {e}")
            return {"success": False, "message": str(e)}


class SelfHostedForumPoster(SocialMediaPoster):
    """Poster for self-hosted forums."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "Self-hosted Forum"
        
        # Forum configuration
        self.forum_url = config.get("forum_url", "")
        self.api_endpoint = config.get("api_endpoint", "/api/posts")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.api_key = config.get("api_key", "")
        self.forum_type = config.get("forum_type", "generic")  # generic, discourse, phpbb, etc.
        
        # Authentication token
        self.auth_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with the forum."""
        if not self.forum_url:
            logger.error("Missing forum URL")
            return False
        
        # If API key is provided, use it directly
        if self.api_key:
            self.auth_token = self.api_key
            logger.info("Using provided API key for forum authentication")
            return True
        
        # Otherwise, try to authenticate with username/password
        if not self.username or not self.password:
            logger.error("Missing forum credentials")
            return False
        
        try:
            # Authentication endpoint depends on forum type
            if self.forum_type == "discourse":
                auth_url = f"{self.forum_url}/session"
                payload = {
                    "login": self.username,
                    "password": self.password
                }
            else:
                # Generic authentication
                auth_url = f"{self.forum_url}/api/auth"
                payload = {
                    "username": self.username,
                    "password": self.password
                }
            
            response = requests.post(auth_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract token based on forum type
                if self.forum_type == "discourse":
                    self.auth_token = response.cookies.get("_t")
                else:
                    self.auth_token = data.get("token")
                
                if self.auth_token:
                    logger.info("Forum authentication successful")
                    return True
                else:
                    logger.error("Authentication succeeded but no token received")
                    return False
            else:
                logger.error(f"Forum authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error authenticating with forum: {e}")
            return False
    
    def post(self, title: str, content: str, image_path: str = "", url: str = "") -> Dict[str, Any]:
        """Post to the forum."""
        if not self.auth_token and not self.authenticate():
            return {"success": False, "message": "Authentication failed"}
        
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authentication
            if self.forum_type == "discourse":
                headers["X-CSRF-Token"] = self.auth_token
                cookies = {"_t": self.auth_token}
            else:
                headers["Authorization"] = f"Bearer {self.auth_token}"
                cookies = {}
            
            # Prepare content
            formatted_content = content
            
            # Add image if available
            if image_path and os.path.exists(image_path):
                # For Discourse
                if self.forum_type == "discourse":
                    # First upload the image
                    with open(image_path, "rb") as img_file:
                        files = {"file": img_file}
                        upload_response = requests.post(
                            f"{self.forum_url}/uploads.json",
                            headers={"X-CSRF-Token": self.auth_token},
                            cookies=cookies,
                            files=files
                        )
                        
                        if upload_response.status_code == 200:
                            upload_data = upload_response.json()
                            image_url = upload_data.get("url")
                            if image_url:
                                formatted_content = f"![image]({image_url})\n\n{formatted_content}"
                else:
                    # For other forums, we might need to use multipart/form-data
                    # This is a simplified approach
                    logger.warning("Image upload for generic forums not fully implemented")
            
            # Add URL if available
            if url:
                formatted_content += f"\n\nSource: {url}"
            
            # Prepare payload based on forum type
            if self.forum_type == "discourse":
                post_url = f"{self.forum_url}/posts"
                payload = {
                    "title": title,
                    "raw": formatted_content,
                    "category": self.config.get("category_id", 1)
                }
            else:
                # Generic forum API
                post_url = f"{self.forum_url}{self.api_endpoint}"
                payload = {
                    "title": title,
                    "content": formatted_content,
                    "category_id": self.config.get("category_id", 1)
                }
            
            # Make the request
            response = requests.post(
                post_url,
                headers=headers,
                cookies=cookies,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get("id") or data.get("post_id")
                
                logger.info(f"Posted to forum: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "url": f"{self.forum_url}/t/{post_id}" if self.forum_type == "discourse" else f"{self.forum_url}/posts/{post_id}"
                }
            else:
                logger.error(f"Forum post failed: {response.status_code} - {response.text}")
                return {"success": False, "message": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error posting to forum: {e}")
            return {"success": False, "message": str(e)}


class InstagramPoster(SocialMediaPoster):
    """Poster for Instagram."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.platform_name = "Instagram"
        self.client = None
        
        # Required credentials
        self.username = config.get("username", "")
        self.password = config.get("password", "")
    
    def authenticate(self) -> bool:
        """Authenticate with Instagram."""
        if not self.username or not self.password:
            logger.error("Missing Instagram credentials")
            return False
        
        try:
            # Initialize the client
            self.client = InstagrapiClient()
            
            # Login
            login_result = self.client.login(self.username, self.password)
            
            if login_result:
                logger.info("Instagram authentication successful")
                return True
            else:
                logger.error("Instagram authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Instagram authentication error: {e}")
            return False
    
    def format_content(self, title: str, content: str, question: str = "", url: str = "") -> str:
        """Format content for Instagram."""
        # Instagram captions
        formatted = f"{title}\n\n{content[:1000]}"  # Limit content length
        
        if question:
            formatted += f"\n\n{question}"
            
        # Add hashtags
        hashtags = self._generate_hashtags(title, content)
        if hashtags:
            formatted += f"\n\n{hashtags}"
            
        return formatted
    
    def _generate_hashtags(self, title: str, content: str) -> str:
        """Generate relevant hashtags from title and content."""
        # Extract potential hashtag words
        words = set()
        for text in [title, content]:
            # Split by spaces and remove punctuation
            for word in text.split():
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 3:  # Only use words longer than 3 characters
                    words.add(word.lower())
        
        # Select up to 10 words for hashtags
        hashtag_words = list(words)[:10]
        
        # Format as hashtags
        hashtags = ' '.join([f"#{word}" for word in hashtag_words])
        
        return hashtags
    
    def post(self, title: str, content: str, image_path: str = "", url: str = "") -> Dict[str, Any]:
        """Post to Instagram."""
        if not self.client:
            if not self.authenticate():
                return {"success": False, "message": "Authentication failed"}
        
        if not image_path or not os.path.exists(image_path):
            return {"success": False, "message": "Image is required for Instagram posts"}
        
        try:
            # Format the caption
            caption = self.format_content(title, content)
            
            # Upload the photo
            media = self.client.photo_upload(
                image_path,
                caption=caption
            )
            
            logger.info(f"Posted to Instagram: {media.id}")
            return {
                "success": True,
                "post_id": media.id,
                "url": f"https://www.instagram.com/p/{media.code}/"
            }
                
        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            return {"success": False, "message": str(e)}


class DiscordPoster(SocialMediaPoster):
    def __init__(self, config):
        super().__init__(config)
        self.url = config.get("webhook_url", "")
    def authenticate(self): return bool(self.url)
    def post(self, title, content, image_path="", url=""):
        data = {"embeds": [{"title": title, "description": content, "url": url}]}
        if image_path: data["embeds"][0]["image"] = {"url": f"attachment://{os.path.basename(image_path)}"}
        files = {"file": open(image_path, "rb")} if image_path else None
        r = requests.post(self.url, data={"payload_json": json.dumps(data)}, files=files)
        return {"success": r.status_code < 300, "message": r.text}

class SocialMediaPosterFactory:
    """Factory for creating social media posters."""
    
    @staticmethod
    def create_poster(platform: str, config: Dict[str, Any]) -> SocialMediaPoster:
        """
        Create a social media poster based on the platform.
        
        Args:
            platform: Platform to create poster for (twitter, reddit, forum, instagram)
            config: Configuration for the poster
            
        Returns:
            SocialMediaPoster instance
        """
        if platform == "twitter":
            return TwitterPoster(config)
        elif platform == "reddit":
            return RedditPoster(config)
        elif platform == "forum":
            return SelfHostedForumPoster(config)
        elif platform == "instagram":
            return InstagramPoster(config)
        elif platform == "discord":
            return DiscordPoster(config)
        else:
            raise ValueError(f"Unknown platform: {platform}")


class SocialMediaManager:
    """Manager for coordinating posting to multiple platforms."""
    
    def __init__(self, config_path: str = None):
        self.posters = {}
        self.config = {}
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Initialize posters from config
            self._init_posters_from_config()
    
    def _init_posters_from_config(self):
        """Initialize posters from configuration file."""
        for platform, platform_config in self.config.get("platforms", {}).items():
            if platform_config.get("enabled", False):
                try:
                    poster = SocialMediaPosterFactory.create_poster(platform, platform_config)
                    self.posters[platform] = poster
                    logger.info(f"Initialized poster for {platform}")
                except Exception as e:
                    logger.error(f"Error creating poster for {platform}: {e}")
    
    def add_poster(self, platform: str, config: Dict[str, Any]):
        """
        Add a poster for a specific platform.
        
        Args:
            platform: Platform name (twitter, reddit, forum, instagram)
            config: Configuration for the platform
        """
        try:
            poster = SocialMediaPosterFactory.create_poster(platform, config)
            self.posters[platform] = poster
            logger.info(f"Added poster for {platform}")
        except Exception as e:
            logger.error(f"Error adding poster for {platform}: {e}")
    
    def post_to_platform(self, platform: str, news_item) -> Dict[str, Any]:
        """
        Post a news item to a specific platform.
        
        Args:
            platform: Platform to post to
            news_item: NewsItem object
            
        Returns:
            Dictionary with post status and details
        """
        if platform not in self.posters:
            return {"success": False, "message": f"No poster configured for {platform}"}
        
        poster = self.posters[platform]
        
        try:
            # Extract required fields from news item
            title = news_item.title if hasattr(news_item, 'title') else ""
            content = news_item.summary if hasattr(news_item, 'summary') else ""
            question = news_item.question if hasattr(news_item, 'question') else ""
            url = news_item.url if hasattr(news_item, 'url') else ""
            image_path = news_item.generated_image_path if hasattr(news_item, 'generated_image_path') else ""
            
            # Format content with question
            formatted_content = poster.format_content(title, content, question, url)
            
            # Post to the platform
            result = poster.post(title, formatted_content, image_path, url)
            
            # Add platform info to result
            result["platform"] = platform
            
            return result
            
        except Exception as e:
            logger.error(f"Error posting to {platform}: {e}")
            return {"success": False, "platform": platform, "message": str(e)}
    
    def post_to_all_platforms(self, news_item) -> List[Dict[str, Any]]:
        """
        Post a news item to all configured platforms.
        
        Args:
            news_item: NewsItem object
            
        Returns:
            List of dictionaries with post status and details for each platform
        """
        results = []
        
        for platform in self.posters:
            try:
                result = self.post_to_platform(platform, news_item)
                results.append(result)
                
                # Add a small delay between posts to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in post_to_all_platforms for {platform}: {e}")
                results.append({
                    "success": False,
                    "platform": platform,
                    "message": str(e)
                })
        
        return results
    
    def save_posting_results(self, news_item, results: List[Dict[str, Any]], output_file: str):
        """
        Save posting results to a JSON file.
        
        Args:
            news_item: NewsItem object
            results: List of posting results
            output_file: Path to output file
        """
        # Create a record with news item details and posting results
        record = {
            "news_item": {
                "title": news_item.title if hasattr(news_item, 'title') else "",
                "url": news_item.url if hasattr(news_item, 'url') else "",
                "summary": news_item.summary if hasattr(news_item, 'summary') else "",
                "question": news_item.question if hasattr(news_item, 'question') else "",
                "image_path": news_item.generated_image_path if hasattr(news_item, 'generated_image_path') else ""
            },
            "posting_time": datetime.now().isoformat(),
            "results": results
        }
        
        # Append to existing file or create new one
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    
                data.append(record)
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Error appending to existing file: {e}")
                # Create new file as fallback
                with open(output_file, 'w') as f:
                    json.dump([record], f, indent=2)
        else:
            with open(output_file, 'w') as f:
                json.dump([record], f, indent=2)
        
        logger.info(f"Saved posting results to {output_file}")


# Example usage
if __name__ == "__main__":
    # Sample news item (mock)
    class MockNewsItem:
        def __init__(self, title, summary, url, question, image_path):
            self.title = title
            self.summary = summary
            self.url = url
            self.question = question
            self.generated_image_path = image_path
    
    # Create a sample news item
    sample_news = MockNewsItem(
        "Climate Change Accelerates Melting of Arctic Ice",
        "Scientists have observed an alarming acceleration in the melting of Arctic ice caps over the past decade.",
        "https://example.com/news/climate-change",
        "What actions can individuals take to help combat climate change?",
        "/path/to/image.jpg"  # This path won't exist in testing
    )
    
    # Create a social media manager
    manager = SocialMediaManager()
    
    # Add a mock Twitter poster for testing
    manager.add_poster("twitter", {
        "consumer_key": "mock_key",
        "consumer_secret": "mock_secret",
        "access_token": "mock_token",
        "access_token_secret": "mock_token_secret"
    })
    
    # Try to post (this will fail with mock credentials)
    results = manager.post_to_all_platforms(sample_news)
    
    # Print results
    for result in results:
        print(f"Platform: {result.get('platform')}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print("-" * 50)

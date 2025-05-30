"""
News Bot - Image Generator Module

This module contains classes for generating images based on news content:
1. Image Generator - Creates images based on news content
2. Image Manager - Coordinates image generation and storage
"""

import os
import logging
import re
import random
import hashlib
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageGenerator(ABC):
    """Abstract base class for image generators."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = config.get("output_dir", "images")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    @abstractmethod
    def generate(self, topic: str, text: str = "", image_url: str = "") -> str:
        """
        Generate an image based on the topic and optional text/image.
        
        Args:
            topic: Main topic for the image
            text: Optional text to incorporate
            image_url: Optional URL of an image to use as reference
            
        Returns:
            Path to the generated image
        """
        pass


class SimpleImageGenerator(ImageGenerator):
    """
    Simple image generator that creates text-based images.
    This is a fallback when more advanced image generation is not available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.width = config.get("width", 1200)
        self.height = config.get("height", 630)
        self.font_path = config.get("font_path", None)
        self.background_colors = config.get("background_colors", [
            (25, 26, 36),    # Dark blue
            (53, 59, 72),    # Dark gray
            (47, 54, 64),    # Slate
            (46, 134, 193),  # Blue
            (40, 116, 166),  # Dark blue
            (17, 122, 101),  # Dark green
            (120, 40, 140),  # Purple
            (146, 43, 33),   # Dark red
        ])
        
        # Try to find a system font if none specified
        if not self.font_path or not os.path.exists(self.font_path):
            self._find_system_font()
    
    def _find_system_font(self):
        """Find a suitable system font."""
        common_font_paths = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            # macOS
            "/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Helvetica.ttf",
            # Windows
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
        ]
        
        for path in common_font_paths:
            if os.path.exists(path):
                self.font_path = path
                logger.info(f"Using system font: {path}")
                return
        
        logger.warning("No system font found. Text rendering may be limited.")
        self.font_path = None
    
    def _create_gradient_background(self, width, height, color1, color2):
        """Create a gradient background."""
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            mask_data.extend([int(255 * (y / height))] * width)
        
        mask.putdata(mask_data)
        return Image.composite(base, top, mask)
    
    def _add_overlay(self, image, opacity=0.3):
        """Add a semi-transparent overlay to make text more readable."""
        overlay = Image.new('RGBA', image.size, (0, 0, 0, int(255 * opacity)))
        return Image.alpha_composite(image.convert('RGBA'), overlay)
    
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width = font.getlength(test_line)
            
            if width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def generate(self, topic: str, text: str = "", image_url: str = "") -> str:
        """
        Generate a simple text-based image.
        
        Args:
            topic: Main topic for the image
            text: Optional text to incorporate
            image_url: Optional URL of an image to use as reference
            
        Returns:
            Path to the generated image
        """
        try:
            # Use topic as main text if no text provided
            if not text:
                text = topic
            
            # Create a unique filename based on content
            content_hash = hashlib.md5(f"{topic}_{text}_{datetime.now()}".encode()).hexdigest()[:10]
            filename = f"{content_hash}.png"
            output_path = os.path.join(self.output_dir, filename)
            
            # Try to use a reference image if provided
            if image_url:
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        # Resize to target dimensions
                        img = img.resize((self.width, self.height), Image.LANCZOS)
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        # Apply blur for aesthetic effect
                        img = img.filter(ImageFilter.GaussianBlur(radius=3))
                    else:
                        raise Exception(f"Failed to download image: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error using reference image: {e}")
                    img = None
            else:
                img = None
            
            # If no image could be loaded, create a gradient background
            if not img:
                color1 = random.choice(self.background_colors)
                color2 = (max(0, color1[0] - 40), max(0, color1[1] - 40), max(0, color1[2] - 40))
                img = self._create_gradient_background(self.width, self.height, color1, color2)
            
            # Add overlay to make text more readable
            img = self._add_overlay(img)
            img = img.convert('RGB')  # Convert back to RGB for saving
            
            # Add text
            draw = ImageDraw.Draw(img)
            
            # Use system font or default to PIL's default font
            if self.font_path:
                try:
                    # Title font (larger)
                    title_font_size = self.height // 10
                    title_font = ImageFont.truetype(self.font_path, title_font_size)
                    
                    # Body font (smaller)
                    body_font_size = self.height // 20
                    body_font = ImageFont.truetype(self.font_path, body_font_size)
                except Exception as e:
                    logger.error(f"Error loading font: {e}")
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()
            else:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
            
            # Draw title (topic)
            title_lines = self._wrap_text(topic, title_font, self.width - 100)
            title_height = len(title_lines) * (title_font.getbbox("Ay")[3] + 10)
            
            y_position = (self.height - title_height) // 3
            for line in title_lines:
                text_width = title_font.getlength(line)
                position = ((self.width - text_width) // 2, y_position)
                # Draw text shadow
                draw.text((position[0] + 2, position[1] + 2), line, font=title_font, fill=(0, 0, 0))
                # Draw text
                draw.text(position, line, font=title_font, fill=(255, 255, 255))
                y_position += title_font.getbbox("Ay")[3] + 10
            
            # Draw body text if different from topic
            if text != topic:
                body_lines = self._wrap_text(text[:200] + "..." if len(text) > 200 else text, 
                                           body_font, self.width - 150)
                
                y_position = self.height - (len(body_lines) * (body_font.getbbox("Ay")[3] + 5)) - 50
                for line in body_lines:
                    text_width = body_font.getlength(line)
                    position = ((self.width - text_width) // 2, y_position)
                    # Draw text shadow
                    draw.text((position[0] + 1, position[1] + 1), line, font=body_font, fill=(0, 0, 0))
                    # Draw text
                    draw.text(position, line, font=body_font, fill=(220, 220, 220))
                    y_position += body_font.getbbox("Ay")[3] + 5
            
            # Save the image
            img.save(output_path, "PNG")
            logger.info(f"Generated image saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return ""


class StockImageGenerator(ImageGenerator):
    """
    Image generator that searches for and downloads relevant stock images.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.search_url = config.get("search_url", "https://pixabay.com/api/")
        self.fallback_generator = SimpleImageGenerator(config)
    
    def generate(self, topic: str, text: str = "", image_url: str = "") -> str:
        """
        Generate an image by searching for and downloading a relevant stock image.
        
        Args:
            topic: Main topic for the image
            text: Optional text to incorporate
            image_url: Optional URL of an image to use as reference
            
        Returns:
            Path to the generated image
        """
        # If image_url is provided, use it directly
        if image_url:
            try:
                # Create a unique filename
                content_hash = hashlib.md5(f"{topic}_{image_url}".encode()).hexdigest()[:10]
                filename = f"{content_hash}.jpg"
                output_path = os.path.join(self.output_dir, filename)
                
                # Download the image
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    # Resize if needed
                    if img.width > 1200 or img.height > 630:
                        img.thumbnail((1200, 630), Image.LANCZOS)
                    # Save the image
                    img.save(output_path)
                    logger.info(f"Downloaded image saved to {output_path}")
                    return output_path
                else:
                    logger.warning(f"Failed to download image: {response.status_code}")
            except Exception as e:
                logger.error(f"Error downloading image: {e}")
        
        # If no API key or image_url failed, use fallback generator
        if not self.api_key:
            logger.warning("No API key for stock images, using fallback generator")
            return self.fallback_generator.generate(topic, text)
        
        try:
            # Search for images related to the topic
            search_term = topic.replace(" ", "+")
            params = {
                "key": self.api_key,
                "q": search_term,
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 5
            }
            
            response = requests.get(self.search_url, params=params)
            data = response.json()
            
            if response.status_code == 200 and data.get("hits"):
                # Get the first image
                image_data = data["hits"][0]
                image_url = image_data.get("webformatURL")
                
                if image_url:
                    # Create a unique filename
                    content_hash = hashlib.md5(f"{topic}_{image_url}".encode()).hexdigest()[:10]
                    filename = f"{content_hash}.jpg"
                    output_path = os.path.join(self.output_dir, filename)
                    
                    # Download the image
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        with open(output_path, "wb") as f:
                            f.write(img_response.content)
                        logger.info(f"Stock image saved to {output_path}")
                        return output_path
            
            # If no images found or download failed, use fallback
            logger.warning("No stock images found, using fallback generator")
            return self.fallback_generator.generate(topic, text)
            
        except Exception as e:
            logger.error(f"Error with stock image API: {e}")
            return self.fallback_generator.generate(topic, text)


class ImageGeneratorFactory:
    """Factory for creating image generators."""
    
    @staticmethod
    def create_generator(generator_type: str, config: Dict[str, Any]) -> ImageGenerator:
        """
        Create an image generator based on the type.
        
        Args:
            generator_type: Type of generator to create (simple, stock)
            config: Configuration for the generator
            
        Returns:
            ImageGenerator instance
        """
        if generator_type == "simple":
            return SimpleImageGenerator(config)
        elif generator_type == "stock":
            return StockImageGenerator(config)
        else:
            logger.warning(f"Unknown generator type: {generator_type}. Using simple generator.")
            return SimpleImageGenerator(config)


class ImageManager:
    """Manager for coordinating image generation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        
        generator_type = config.get("generator_type", "simple")
        generator_config = config.get("generator_config", {
            "output_dir": os.path.join(os.getcwd(), "images"),
            "width": 1200,
            "height": 630
        })
        
        self.generator = ImageGeneratorFactory.create_generator(generator_type, generator_config)
    
    def generate_image_for_news_item(self, news_item):
        """
        Generate an image for a news item.
        
        Args:
            news_item: NewsItem object
            
        Returns:
            Updated NewsItem with generated_image_path set
        """
        try:
            # Use existing image URL if available
            image_url = news_item.image_url if hasattr(news_item, 'image_url') else ""
            
            # Generate text for image from title and summary
            title = news_item.title if hasattr(news_item, 'title') else ""
            summary = news_item.summary if hasattr(news_item, 'summary') else ""
            
            # Generate the image
            image_path = self.generator.generate(title, summary, image_url)
            
            # Update the news item
            if hasattr(news_item, 'generated_image_path'):
                news_item.generated_image_path = image_path
            
            return news_item
            
        except Exception as e:
            logger.error(f"Error generating image for news item: {e}")
            return news_item
    
    def generate_images_for_news_items(self, news_items):
        """
        Generate images for multiple news items.
        
        Args:
            news_items: List of NewsItem objects
            
        Returns:
            List of updated NewsItem objects
        """
        updated_items = []
        
        for item in news_items:
            try:
                updated_item = self.generate_image_for_news_item(item)
                updated_items.append(updated_item)
            except Exception as e:
                logger.error(f"Error processing news item for image: {e}")
                updated_items.append(item)  # Keep the original item
        
        return updated_items


# Example usage
if __name__ == "__main__":
    # Sample news item (mock)
    class MockNewsItem:
        def __init__(self, title, summary, image_url=""):
            self.title = title
            self.summary = summary
            self.image_url = image_url
            self.generated_image_path = ""
    
    # Create a sample news item
    sample_news = MockNewsItem(
        "Climate Change Accelerates Melting of Arctic Ice",
        "Scientists have observed an alarming acceleration in the melting of Arctic ice caps over the past decade. According to a new study, the rate of ice loss has increased by 65% since 2010.",
        "https://example.com/arctic_ice.jpg"  # This URL won't work in testing
    )
    
    # Create an image manager
    image_manager = ImageManager()
    
    # Generate an image for the news item
    processed_news = image_manager.generate_image_for_news_item(sample_news)
    
    # Print results
    print(f"Title: {processed_news.title}")
    print(f"Generated Image: {processed_news.generated_image_path}")

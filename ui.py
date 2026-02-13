"""
News Bot - User Interface Module

This module provides a simple web interface for the News Bot:
1. Topic Configuration
2. Destination Selection
3. Manual Execution
"""

import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from main import NewsBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="News Bot UI")

# Create templates directory
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global bot instance
news_bot = None
config_path = "config.json"

# Default configuration
default_config = {
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

# Create HTML templates
def create_templates():
    """Create HTML templates for the UI."""
    # Index page
    index_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>News Bot</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 800px;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-top: 20px;
            }
            h1 {
                color: #0d6efd;
                margin-bottom: 20px;
            }
            .nav-tabs {
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .platform-card {
                margin-bottom: 15px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
            }
            .platform-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .results-container {
                margin-top: 30px;
            }
            .result-item {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            .platform-result {
                margin-top: 10px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .success {
                color: #198754;
            }
            .error {
                color: #dc3545;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>News Bot</h1>
            
            <ul class="nav nav-tabs" id="myTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="run-tab" data-bs-toggle="tab" data-bs-target="#run" type="button" role="tab" aria-controls="run" aria-selected="true">Run Bot</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="platforms-tab" data-bs-toggle="tab" data-bs-target="#platforms" type="button" role="tab" aria-controls="platforms" aria-selected="false">Configure Platforms</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="settings-tab" data-bs-toggle="tab" data-bs-target="#settings" type="button" role="tab" aria-controls="settings" aria-selected="false">Settings</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="scheduling-tab" data-bs-toggle="tab" data-bs-target="#scheduling" type="button" role="tab" aria-controls="scheduling" aria-selected="false">Scheduling</button>
                </li>
            </ul>
            
            <div class="tab-content" id="myTabContent">
                <!-- Run Bot Tab -->
                <div class="tab-pane fade show active" id="run" role="tabpanel" aria-labelledby="run-tab">
                    <form action="/run" method="post">
                        <div class="form-group">
                            <label for="topic" class="form-label">Topic:</label>
                            <input type="text" class="form-control" id="topic" name="topic" required placeholder="Enter news topic (e.g., climate change, technology, sports)">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Select Platforms:</label>
                            {% for platform in platforms %}
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="selected_platforms" value="{{ platform }}" id="platform-{{ platform }}" {% if platform in enabled_platforms %}checked{% endif %}>
                                <label class="form-check-label" for="platform-{{ platform }}">
                                    {{ platform|capitalize }}
                                </label>
                            </div>
                            {% endfor %}
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Run News Bot</button>
                    </form>
                    
                    {% if results %}
                    <div class="results-container">
                        <h3>Results</h3>
                        {% for result in results %}
                        <div class="result-item">
                            <h4>{{ result.news_item.title }}</h4>
                            <p><strong>Summary:</strong> {{ result.news_item.summary }}</p>
                            <p><strong>Question:</strong> {{ result.news_item.question }}</p>
                            {% if result.news_item.generated_image_path %}
                            <p><strong>Image:</strong> {{ result.news_item.generated_image_path }}</p>
                            {% endif %}
                            
                            <h5>Posting Results:</h5>
                            {% for posting in result.posting_results %}
                            <div class="platform-result">
                                <p>
                                    <strong>{{ posting.platform|capitalize }}:</strong>
                                    <span class="{% if posting.success %}success{% else %}error{% endif %}">
                                        {% if posting.success %}Success{% else %}Failed{% endif %}
                                    </span>
                                </p>
                                {% if posting.url %}
                                <p><strong>URL:</strong> <a href="{{ posting.url }}" target="_blank">{{ posting.url }}</a></p>
                                {% endif %}
                                {% if posting.message and not posting.success %}
                                <p><strong>Error:</strong> {{ posting.message }}</p>
                                {% endif %}
                            </div>
                            {% endfor %}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                
                <!-- Configure Platforms Tab -->
                <div class="tab-pane fade" id="platforms" role="tabpanel" aria-labelledby="platforms-tab">
                    <h3>Social Media Platforms</h3>
                    
                    <div class="platform-card">
                        <div class="platform-header">
                            <h4>X (Twitter)</h4>
                            <a href="/platform/twitter" class="btn btn-sm btn-primary">Configure</a>
                        </div>
                        <p>Status: {% if "twitter" in enabled_platforms %}Configured{% else %}Not Configured{% endif %}</p>
                    </div>
                    
                    <div class="platform-card">
                        <div class="platform-header">
                            <h4>Reddit</h4>
                            <a href="/platform/reddit" class="btn btn-sm btn-primary">Configure</a>
                        </div>
                        <p>Status: {% if "reddit" in enabled_platforms %}Configured{% else %}Not Configured{% endif %}</p>
                    </div>
                    
                    <div class="platform-card">
                        <div class="platform-header">
                            <h4>Self-hosted Forum</h4>
                            <a href="/platform/forum" class="btn btn-sm btn-primary">Configure</a>
                        </div>
                        <p>Status: {% if "forum" in enabled_platforms %}Configured{% else %}Not Configured{% endif %}</p>
                    </div>
                    
                    <div class="platform-card">
                        <div class="platform-header">
                            <h4>Instagram</h4>
                            <a href="/platform/instagram" class="btn btn-sm btn-primary">Configure</a>
                        </div>
                        <p>Status: {% if "instagram" in enabled_platforms %}Configured{% else %}Not Configured{% endif %}</p>
                    </div>
                </div>
                
                <!-- Settings Tab -->
                <div class="tab-pane fade" id="settings" role="tabpanel" aria-labelledby="settings-tab">
                    <h3>Bot Settings</h3>
                    
                    <form action="/settings" method="post">
                        <div class="form-group">
                            <label for="max_results" class="form-label">Max Results Per Source:</label>
                            <input type="number" class="form-control" id="max_results" name="max_results" value="{{ config.scraper.max_results_per_source }}" min="1" max="10">
                        </div>
                        
                        <div class="form-group">
                            <label for="max_sentences" class="form-label">Max Sentences in Summary:</label>
                            <input type="number" class="form-control" id="max_sentences" name="max_sentences" value="{{ config.processor.summarizer.max_sentences }}" min="1" max="5">
                        </div>
                        
                        <div class="form-group">
                            <label for="summarization_method" class="form-label">Summarization Method:</label>
                            <select class="form-select" id="summarization_method" name="summarization_method">
                                <option value="extractive" {% if config.processor.summarizer.method == "extractive" %}selected{% endif %}>Extractive</option>
                                <option value="abstractive" {% if config.processor.summarizer.method == "abstractive" %}selected{% endif %}>Abstractive</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="image_generator_type" class="form-label">Image Generator Type:</label>
                            <select class="form-select" id="image_generator_type" name="image_generator_type">
                                <option value="simple" {% if config.image_generator.generator_type == "simple" %}selected{% endif %}>Simple</option>
                                <option value="stock" {% if config.image_generator.generator_type == "stock" %}selected{% endif %}>Stock</option>
                            </select>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Save Settings</button>
                    </form>
                </div>
                
                <!-- Scheduling Tab -->
                <div class="tab-pane fade" id="scheduling" role="tabpanel" aria-labelledby="scheduling-tab">
                    <h3>Bot Scheduling</h3>
                    <form action="/schedule" method="post">
                        <div class="form-group">
                            <label for="schedule_topic" class="form-label">Topic to Schedule:</label>
                            <input type="text" class="form-control" id="schedule_topic" name="topic" value="{{ config.scheduling.topic if config.scheduling else '' }}" placeholder="e.g., AI news">
                        </div>
                        <div class="form-group">
                            <label for="cron" class="form-label">Cron Expression:</label>
                            <input type="text" class="form-control" id="cron" name="cron" value="{{ config.scheduling.cron if config.scheduling else '0 0 * * *' }}" placeholder="0 0 * * * (Daily at midnight)">
                        </div>
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" name="enabled" id="sched_enabled" {% if config.scheduling and config.scheduling.enabled %}checked{% endif %}>
                            <label class="form-check-label" for="sched_enabled">Enable Schedule</label>
                        </div>
                        <button type="submit" class="btn btn-primary">Save Schedule</button>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Platform configuration page
    platform_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Configure {{ platform|capitalize }} - News Bot</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
        <style>
            body {
                padding: 20px;
                background-color: #f8f9fa;
            }
            .container {
                max-width: 800px;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-top: 20px;
            }
            h1 {
                color: #0d6efd;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Configure {{ platform|capitalize }}</h1>
            
            <form action="/platform/{{ platform }}" method="post">
                <input type="hidden" name="platform" value="{{ platform }}">
                
                <div class="form-check mb-4">
                    <input class="form-check-input" type="checkbox" name="enabled" id="enabled" {% if config.enabled %}checked{% endif %}>
                    <label class="form-check-label" for="enabled">
                        Enable {{ platform|capitalize }}
                    </label>
                </div>
                
                {% if platform == "twitter" %}
                <div class="form-group">
                    <label for="consumer_key" class="form-label">Consumer Key:</label>
                    <input type="text" class="form-control" id="consumer_key" name="consumer_key" value="{{ config.consumer_key }}">
                </div>
                <div class="form-group">
                    <label for="consumer_secret" class="form-label">Consumer Secret:</label>
                    <input type="password" class="form-control" id="consumer_secret" name="consumer_secret" value="{{ config.consumer_secret }}">
                </div>
                <div class="form-group">
                    <label for="access_token" class="form-label">Access Token:</label>
                    <input type="text" class="form-control" id="access_token" name="access_token" value="{{ config.access_token }}">
                </div>
                <div class="form-group">
                    <label for="access_token_secret" class="form-label">Access Token Secret:</label>
                    <input type="password" class="form-control" id="access_token_secret" name="access_token_secret" value="{{ config.access_token_secret }}">
                </div>
                {% elif platform == "reddit" %}
                <div class="form-group">
                    <label for="client_id" class="form-label">Client ID:</label>
                    <input type="text" class="form-control" id="client_id" name="client_id" value="{{ config.client_id }}">
                </div>
                <div class="form-group">
                    <label for="client_secret" class="form-label">Client Secret:</label>
                    <input type="password" class="form-control" id="client_secret" name="client_secret" value="{{ config.client_secret }}">
                </div>
                <div class="form-group">
                    <label for="username" class="form-label">Username:</label>
                    <input type="text" class="form-control" id="username" name="username" value="{{ config.username }}">
                </div>
                <div class="form-group">
                    <label for="password" class="form-label">Password:</label>
                    <input type="password" class="form-control" id="password" name="password" value="{{ config.password }}">
                </div>
                <div class="form-group">
                    <label for="subreddit" class="form-label">Subreddit:</label>
                    <input type="text" class="form-control" id="subreddit" name="subreddit" value="{{ config.subreddit }}">
                </div>
                {% elif platform == "forum" %}
                <div class="form-group">
                    <label for="forum_url" class="form-label">Forum URL:</label>
                    <input type="text" class="form-control" id="forum_url" name="forum_url" value="{{ config.forum_url }}">
                </div>
                <div class="form-group">
                    <label for="forum_type" class="form-label">Forum Type:</label>
                    <select class="form-select" id="forum_type" name="forum_type">
                        <option value="generic" {% if config.forum_type == "generic" %}selected{% endif %}>Generic</option>
                        <option value="discourse" {% if config.forum_type == "discourse" %}selected{% endif %}>Discourse</option>
                        <option value="phpbb" {% if config.forum_type == "phpbb" %}selected{% endif %}>phpBB</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="username" class="form-label">Username:</label>
                    <input type="text" class="form-control" id="username" name="username" value="{{ config.username }}">
                </div>
                <div class="form-group">
                    <label for="password" class="form-label">Password:</label>
                    <input type="password" class="form-control" id="password" name="password" value="{{ config.password }}">
                </div>
                <div class="form-group">
                    <label for="api_key" class="form-label">API Key (if available):</label>
                    <input type="password" class="form-control" id="api_key" name="api_key" value="{{ config.api_key }}">
                </div>
                <div class="form-group">
                    <label for="category_id" class="form-label">Category ID:</label>
                    <input type="text" class="form-control" id="category_id" name="category_id" value="{{ config.category_id }}">
                </div>
                {% elif platform == "instagram" %}
                <div class="form-group">
                    <label for="username" class="form-label">Username:</label>
                    <input type="text" class="form-control" id="username" name="username" value="{{ config.username }}">
                </div>
                <div class="form-group">
                    <label for="password" class="form-label">Password:</label>
                    <input type="password" class="form-control" id="password" name="password" value="{{ config.password }}">
                </div>
                {% endif %}
                
                <div class="mt-4">
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                    <a href="/" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    
    # Write templates to files
    with open("templates/index.html", "w") as f:
        f.write(index_html)
    
    with open("templates/platform.html", "w") as f:
        f.write(platform_html)
    
    logger.info("Created HTML templates")

# Initialize the bot
def init_bot():
    """Initialize the News Bot."""
    global news_bot
    
    # Create templates if they don't exist
    if not os.path.exists("templates/index.html"):
        create_templates()
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
    
    # Initialize the bot
    news_bot = NewsBot(config_path)
    
    logger.info("Initialized News Bot")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    if news_bot is None:
        init_bot()
    
    # Get enabled platforms
    enabled_platforms = []
    for platform, config in news_bot.config.get("poster", {}).get("platforms", {}).items():
        if config.get("enabled", False):
            enabled_platforms.append(platform)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "platforms": ["twitter", "reddit", "forum", "instagram"],
            "enabled_platforms": enabled_platforms,
            "config": news_bot.config,
            "results": []
        }
    )

@app.post("/run", response_class=HTMLResponse)
async def run_bot(request: Request, topic: str = Form(...), selected_platforms: List[str] = Form([])):
    """Run the News Bot."""
    if news_bot is None:
        init_bot()
    
    # Update enabled platforms
    for platform in ["twitter", "reddit", "forum", "instagram"]:
        if platform in news_bot.config.get("poster", {}).get("platforms", {}):
            news_bot.config["poster"]["platforms"][platform]["enabled"] = platform in selected_platforms
    
    # Save config
    news_bot.save_config(config_path)
    
    # Run the bot
    results = news_bot.run(topic)
    
    # Get enabled platforms
    enabled_platforms = []
    for platform, config in news_bot.config.get("poster", {}).get("platforms", {}).items():
        if config.get("enabled", False):
            enabled_platforms.append(platform)
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "platforms": ["twitter", "reddit", "forum", "instagram"],
            "enabled_platforms": enabled_platforms,
            "config": news_bot.config,
            "results": results
        }
    )

@app.get("/platform/{platform}", response_class=HTMLResponse)
async def get_platform(request: Request, platform: str):
    """Render the platform configuration page."""
    if news_bot is None:
        init_bot()
    
    if platform not in ["twitter", "reddit", "forum", "instagram"]:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # Get platform config
    config = news_bot.config.get("poster", {}).get("platforms", {}).get(platform, {})
    
    return templates.TemplateResponse(
        "platform.html", 
        {
            "request": request, 
            "platform": platform,
            "config": config
        }
    )

@app.post("/platform/{platform}", response_class=RedirectResponse)
async def save_platform(
    request: Request, 
    platform: str,
    enabled: bool = Form(False),
    # Twitter
    consumer_key: str = Form(""),
    consumer_secret: str = Form(""),
    access_token: str = Form(""),
    access_token_secret: str = Form(""),
    # Reddit
    client_id: str = Form(""),
    client_secret: str = Form(""),
    username: str = Form(""),
    password: str = Form(""),
    subreddit: str = Form(""),
    # Forum
    forum_url: str = Form(""),
    forum_type: str = Form("generic"),
    api_key: str = Form(""),
    category_id: str = Form("1"),
    # Instagram - username and password already covered
):
    """Save platform configuration."""
    if news_bot is None:
        init_bot()
    
    if platform not in ["twitter", "reddit", "forum", "instagram"]:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # Create platform config
    if platform == "twitter":
        config = {
            "enabled": enabled,
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret
        }
    elif platform == "reddit":
        config = {
            "enabled": enabled,
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "subreddit": subreddit,
            "user_agent": "NewsBot/1.0"
        }
    elif platform == "forum":
        config = {
            "enabled": enabled,
            "forum_url": forum_url,
            "forum_type": forum_type,
            "username": username,
            "password": password,
            "api_key": api_key,
            "category_id": category_id
        }
    elif platform == "instagram":
        config = {
            "enabled": enabled,
            "username": username,
            "password": password
        }
    
    # Update bot config
    if "poster" not in news_bot.config:
        news_bot.config["poster"] = {"platforms": {}}
    if "platforms" not in news_bot.config["poster"]:
        news_bot.config["poster"]["platforms"] = {}
    
    news_bot.config["poster"]["platforms"][platform] = config
    
    # Add platform to bot
    if enabled:
        news_bot.add_platform(platform, config)
    
    # Save config
    news_bot.save_config(config_path)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/settings", response_class=RedirectResponse)
async def save_settings(
    request: Request,
    max_results: int = Form(3),
    max_sentences: int = Form(3),
    summarization_method: str = Form("extractive"),
    image_generator_type: str = Form("simple")
):
    """Save bot settings."""
    if news_bot is None:
        init_bot()
    
    # Update config
    news_bot.config["scraper"]["max_results_per_source"] = max_results
    news_bot.config["processor"]["summarizer"]["max_sentences"] = max_sentences
    news_bot.config["processor"]["summarizer"]["method"] = summarization_method
    news_bot.config["image_generator"]["generator_type"] = image_generator_type
    
    # Save config
    news_bot.save_config(config_path)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/schedule", response_class=RedirectResponse)
async def save_schedule(request: Request, topic: str = Form(...), cron: str = Form("0 0 * * *"), enabled: bool = Form(False)):
    if news_bot is None: init_bot()
    news_bot.config["scheduling"] = {"topic": topic, "cron": cron, "enabled": enabled}
    news_bot.save_config(config_path)
    return RedirectResponse(url="/", status_code=303)

def start():
    """Start the UI server."""
    # Initialize the bot
    init_bot()
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

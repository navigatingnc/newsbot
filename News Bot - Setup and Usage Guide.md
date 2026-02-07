# News Bot - Setup and Usage Guide

## Overview

The News Bot is a modular, replicable system designed to scrape news from various sources, summarize content, generate related questions and images, and post to multiple social media platforms and forums. The system is built using an open-source stack and is designed to be easily configurable through a user interface.

## Features

- **News Scraping**: Collects news from Google search, websites, and RSS feeds
- **Content Processing**: Summarizes articles and generates engaging questions
- **Image Generation**: Creates relevant images for each news item
- **Social Media Posting**: Posts to X (Twitter), Reddit, self-hosted forums, and Instagram
- **User Interface**: Web-based interface for configuration and manual execution
- **AI-Guided Improvements**: Framework for AI agents to perform scheduled application enhancements
- **Replicable**: Create multiple bots with different configurations

## System Requirements

- Python 3.8 or higher
- Internet connection
- API credentials for social media platforms (if posting is required)

## Installation

1. Clone the repository or extract the provided files to your desired location
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install the required dependencies:
   ```
   pip install -r src/requirements.txt
   ```

## Configuration

### Using the Web Interface

1. Start the web interface:
   ```
   python src/ui.py
   ```
2. Open your browser and navigate to `http://localhost:8000`
3. Use the interface to configure:
   - Social media platforms
   - Scraping settings
   - Content processing options
   - Image generation settings

### Manual Configuration

You can also configure the bot by editing the `config.json` file directly. The file structure is as follows:

```json
{
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
    "platforms": {
      "twitter": {
        "enabled": true,
        "consumer_key": "YOUR_KEY",
        "consumer_secret": "YOUR_SECRET",
        "access_token": "YOUR_TOKEN",
        "access_token_secret": "YOUR_TOKEN_SECRET"
      },
      "reddit": {
        "enabled": true,
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
        "subreddit": "YOUR_SUBREDDIT",
        "user_agent": "NewsBot/1.0"
      },
      "forum": {
        "enabled": false,
        "forum_url": "https://your-forum.com",
        "forum_type": "discourse",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
        "api_key": "",
        "category_id": "1"
      },
      "instagram": {
        "enabled": false,
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD"
      }
    }
  }
}
```

## Usage

### Using the Web Interface

1. Start the web interface:
   ```
   python src/ui.py
   ```
2. Navigate to the "Run Bot" tab
3. Enter a topic to search for
4. Select the platforms to post to
5. Click "Run News Bot"
6. View the results on the same page

### Using the Command Line

You can also run the bot from the command line:

```
python src/main.py --topic "your topic" --config config.json
```

### Daily Operation

For daily operation, you have several options:

1. **Manual Execution**: Run the bot manually when needed
2. **System Scheduler**:
   - Windows: Use Task Scheduler
   - Linux/Mac: Use cron jobs
   
Example cron job for daily execution at 9 AM:
```
0 9 * * * cd /path/to/news_bot && /path/to/python src/main.py --topic "your topic" --config config.json
```

### AI-Guided Improvements

The News Bot includes a framework for AI agents to automatically improve the application.

1. **AI Improvement Guide**: See `AI_IMPROVEMENT_GUIDE.md` for the full framework.
2. **Configuration**: AI task settings are located in `ai_tasks_config.json`.
3. **Execution**: AI agents can be scheduled to review `todo.md` and implement the next high-priority task.

## Project Structure

```
news_bot/
├── src/
│   ├── main.py           # Main controller
│   ├── scraper.py        # News scraping module
│   ├── processor.py      # Content processing module
│   ├── image_generator.py # Image generation module
│   ├── poster.py         # Social media posting module
│   ├── ui.py             # Web interface
│   └── requirements.txt  # Dependencies
├── docs/
│   ├── architecture.md   # System architecture documentation
│   └── setup.md          # This setup guide
├── images/               # Generated images directory
├── output/               # Output files directory
├── templates/            # UI templates
└── config.json           # Configuration file
```

## Customization

### Adding New News Sources

To add new news sources, modify the `scraper.py` file:

1. For websites, add new entries to the `sites` list in the `WebsiteScraper` class
2. For RSS feeds, add new URLs to the `feeds` list in the `RSSFeedScraper` class

### Adding New Social Media Platforms

To add support for new social media platforms:

1. Create a new class in `poster.py` that inherits from `SocialMediaPoster`
2. Implement the required methods: `authenticate()` and `post()`
3. Add the new platform to the `SocialMediaPosterFactory` class
4. Update the UI to include the new platform

## Troubleshooting

### Common Issues

1. **Authentication Failures**:
   - Verify API credentials are correct
   - Check that API access is enabled for your accounts
   - Ensure you have the necessary permissions

2. **No News Found**:
   - Try a different topic
   - Check internet connectivity
   - Verify scraper configuration

3. **Image Generation Fails**:
   - Ensure the output directory is writable
   - Check for required fonts or dependencies
   - Try using a different image generator type

### Logs

Check the following log files for more information:

- `news_bot.log`: Main application log
- Browser console logs when using the web interface

## Security Considerations

- API keys and credentials are stored in plain text in the configuration file
- Consider using environment variables or a secure credential store in production
- Be mindful of rate limits on social media platforms
- Respect website terms of service when scraping

## License

This project is released under the MIT License.

## Support

For issues, questions, or feature requests, please contact the developer.

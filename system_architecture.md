# News Bot System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                     main.py (NewsBot)               │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │scraper.py│→ │processor.py│→│image_generator.py│  │
│  └──────────┘  └───────────┘  └──────────────────┘  │
│                                        ↓             │
│                                  ┌──────────┐        │
│                                  │poster.py │        │
│                                  └──────────┘        │
└─────────────────────────────────────────────────────┘
         ↑ config: ai_tasks_config.json
```

## Data Flow

1. `main.py` reads config → calls `NewsScraperManager.scrape_news(topic)`
2. Raw `NewsItem` list → `ContentProcessorManager.process_news_items()` → adds `summary`, `question`
3. Processed items → `ImageManager.generate_images_for_news_items()` → adds `generated_image_path`
4. Final items → `SocialMediaManager.post_to_all_platforms()` → returns posting results
5. Each stage persists JSON to `output/{topic}_{stage}.json`

## API Interfaces

| Module | Class | Key Method | Input | Output |
|--------|-------|-----------|-------|--------|
| scraper | `NewsScraperManager` | `scrape_news(topic, max)` | str, int | `List[NewsItem]` |
| processor | `ContentProcessorManager` | `process_news_items(items)` | `List[NewsItem]` | `List[NewsItem]` |
| image_generator | `ImageManager` | `generate_images_for_news_items(items)` | `List[NewsItem]` | `List[NewsItem]` |
| poster | `SocialMediaManager` | `post_to_all_platforms(item)` | `NewsItem` | `List[Dict]` |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.x |
| Scraping | `requests`, `BeautifulSoup`, RSS/Google Search |
| Processing | Extractive summarization (built-in NLP) |
| Image Generation | `Pillow` (simple); DALL-E 3 (planned) |
| Posting | Twitter/X API, Reddit PRAW, Instagram, Forum HTTP |
| Config | JSON (`ai_tasks_config.json`) |
| Logging | Python `logging` → `news_bot.log` |
| UI | `ui.py` (planned) |

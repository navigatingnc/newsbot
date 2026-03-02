# News Bot

A modular Python application that scrapes news by topic, summarizes it, generates follow-up questions, optionally creates images, and can post results to social platforms.

## What this repo contains

- `main.py` — CLI entry point and pipeline orchestration.
- `scraper.py` — news collection from search/web/RSS sources.
- `processor.py` — summarization and question generation.
- `image_generator.py` — image generation for processed items.
- `poster.py` — posting adapters and platform manager.
- `ui.py` — FastAPI-based web UI for running/configuring the bot.
- `ai_tasks_config.json` / `AI_IMPROVEMENT_GUIDE.md` / `todo.md` — scheduled AI improvement workflow and backlog.

## Pipeline overview

For a given topic, the bot executes:

1. **Scrape** news items.
2. **Process** content (summary + question).
3. **Generate images** for items.
4. **Post** to enabled social platforms.
5. **Persist outputs** as JSON files under `output/`.

## Requirements

- Python 3.8+
- `pip`
- Optional API credentials for platforms you enable (Twitter/X, Reddit, forum, Instagram).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick start (CLI)

Run with defaults:

```bash
python main.py --topic "technology"
```

Run with a custom config file:

```bash
python main.py --topic "technology" --config config.json
```

## Run the web UI

```bash
python ui.py
```

Then open `http://localhost:8000`.

## Configuration

- If `--config` is not provided, `main.py` uses built-in defaults.
- The UI reads/writes `config.json` in the repository root.
- Platform posting is only attempted for configured and enabled platforms.

## Output artifacts

- `output/*_raw.json` — scraped input items.
- `output/*_processed.json` — summarized/question-enhanced items.
- `output/*_with_images.json` — items with generated image paths.
- `output/*_posting_results.json` — post success/failure details.
- `images/` — generated images.
- `news_bot.log` — runtime logs.

## Related docs

- `News Bot - Setup and Usage Guide.md`
- `News Bot System Architecture.md`
- `AI_IMPROVEMENT_GUIDE.md`

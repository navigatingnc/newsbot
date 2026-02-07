# AI-Guided Application Improvements

This document serves as a guide for AI agents (like Manus) to perform scheduled tasks that improve the `newsbot` application. By following this structure, the AI can systematically identify, implement, and verify improvements.

## 1. Improvement Cycle

The AI should follow this cycle during each scheduled improvement task:

1.  **Audit**: Review the current state of the application, including `todo.md`, logs, and source code.
2.  **Propose**: Identify a specific improvement or feature from the backlog or through analysis.
3.  **Implement**: Write and test the code changes.
4.  **Verify**: Ensure the changes work as expected and don't break existing functionality.
5.  **Document**: Update `todo.md` and this guide if necessary.

## 2. Priority Areas for Improvement

Based on the current `todo.md`, the following areas are prioritized:

| Priority | Category | Task Description |
| :--- | :--- | :--- |
| **High** | UI/UX | Create a user interface for topic configuration and scheduling. |
| **High** | Testing | Implement comprehensive validation for scraping and summarization. |
| **Medium** | Architecture | Create component diagrams and document API interfaces. |
| **Medium** | Features | Add more news sources and refine image generation prompts. |
| **Low** | Optimization | Improve performance of the scraper and processor. |

## 3. Execution Instructions for AI

> **Guardrail: Efficiency Limit**
> To ensure cost-effectiveness and focus, each improvement task MUST NOT exceed a total of **300 tokens** for the implementation plan and code generation combined. The AI should prioritize concise, high-impact changes.

When triggered for a scheduled improvement task, the AI should:

### Step 1: Context Gathering
```bash
# Check current tasks
cat todo.md

# Check for recent errors
tail -n 100 news_bot.log
```

### Step 2: Implementation Strategy
- Pick the highest priority item from `todo.md` that is not yet completed.
- Create a feature branch for the improvement: `git checkout -b feature/improvement-name`.
- Implement the changes in the relevant modules (`scraper.py`, `processor.py`, etc.).

### Step 3: Verification
- Run the bot with a test topic to ensure stability: `python3 main.py --topic "test"`.
- Check `news_bot.log` for any new warnings or errors.

### Step 4: Finalization
- Update `todo.md` to mark the task as completed.
- Commit and push changes.

## 4. Scheduled Task Configuration

Scheduled tasks should be configured to run periodically (e.g., weekly) to ensure continuous improvement.

**Example Cron Schedule:** `0 0 * * 0` (Every Sunday at midnight)
**Prompt for AI:** "Review the newsbot repository, identify the next high-priority task in todo.md, and implement it to improve the application."

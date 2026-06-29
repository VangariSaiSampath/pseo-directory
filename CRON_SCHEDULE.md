# AI Agent Cron Schedule - Zero Cost Automation

This document outlines the automated content generation schedule using AI agents (Gemini API - free tier).

## Cron Job Schedule (IST - Indian Standard Time)

### Daily Schedule

| Time (IST) | Agent Endpoint | Purpose | Frequency |
|------------|----------------|---------|-----------|
| 02:00 AM | `/api/agent/generate-case-studies` | Generate 3 new case studies | Daily |
| 03:00 AM | `/api/agent/generate-testimonials` | Generate 5 new testimonials | Daily |
| 04:00 AM | `/api/agent/enhance-integrations?count=5` | Add use cases to 5 integrations | Daily |
| 05:00 AM | `/api/agent/enhance-faqs?count=10` | Add FAQs to 10 integrations | Daily |
| 06:00 AM | `/api/agent/daily-blog?count=4` | Publish 4 blog posts | 4x/day (06:00, 10:00, 14:00, 18:00) |
| 10:00 AM | `/api/agent/daily-blog?count=4` | Publish 4 blog posts | 4x/day |
| 14:00 PM | `/api/agent/daily-blog?count=4` | Publish 4 blog posts | 4x/day |
| 18:00 PM | `/api/agent/daily-blog?count=4` | Publish 4 blog posts | 4x/day |
| 20:00 PM | `/api/agent/daily-news?count=4` | Publish 4 news articles | 2x/day (20:00, 23:00) |
| 23:00 PM | `/api/agent/daily-news?count=4` | Publish 4 news articles | 2x/day |

## Setup Instructions

### Option 1: Using Cron (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# AI Content Generation Agents - All times in IST (UTC+5:30)
# Convert to UTC: IST 02:00 = UTC 20:30 (previous day)

# Case Studies - Daily at 02:00 IST (20:30 UTC)
30 20 * * * curl "https://integration-directory.com/api/agent/generate-case-studies?secret=YOUR_SECRET"

# Testimonials - Daily at 03:00 IST (21:30 UTC)
30 21 * * * curl "https://integration-directory.com/api/agent/generate-testimonials?secret=YOUR_SECRET"

# Enhance Integrations - Daily at 04:00 IST (22:30 UTC)
30 22 * * * curl "https://integration-directory.com/api/agent/enhance-integrations?secret=YOUR_SECRET&count=5"

# Enhance FAQs - Daily at 05:00 IST (23:30 UTC)
30 23 * * * curl "https://integration-directory.com/api/agent/enhance-faqs?secret=YOUR_SECRET&count=10"

# Blog Posts - 4x daily at 06:00, 10:00, 14:00, 18:00 IST
# 06:00 IST = 00:30 UTC
30 0 * * * curl "https://integration-directory.com/api/agent/daily-blog?secret=YOUR_SECRET&count=4"
# 10:00 IST = 04:30 UTC
30 4 * * * curl "https://integration-directory.com/api/agent/daily-blog?secret=YOUR_SECRET&count=4"
# 14:00 IST = 08:30 UTC
30 8 * * * curl "https://integration-directory.com/api/agent/daily-blog?secret=YOUR_SECRET&count=4"
# 18:00 IST = 12:30 UTC
30 12 * * * curl "https://integration-directory.com/api/agent/daily-blog?secret=YOUR_SECRET&count=4"

# News Articles - 2x daily at 20:00, 23:00 IST
# 20:00 IST = 14:30 UTC
30 14 * * * curl "https://integration-directory.com/api/agent/daily-news?secret=YOUR_SECRET&count=4"
# 23:00 IST = 17:30 UTC
30 17 * * * curl "https://integration-directory.com/api/agent/daily-news?secret=YOUR_SECRET&count=4"
```

### Option 2: Using Python Scheduler (Alternative)

Create `scheduler.py`:

```python
import asyncio
import httpx
from datetime import datetime
import os

BASE_URL = "https://integration-directory.com"
SECRET = os.environ.get("AGENT_SECRET", "my_local_secret")

async def call_agent(endpoint: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}{endpoint}")
            print(f"[{datetime.now()}] {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now()}] {endpoint}: ERROR - {e}")

async def main():
    while True:
        now = datetime.now()
        
        # Run agents at specific times
        if now.hour == 2 and now.minute == 0:
            await call_agent(f"/api/agent/generate-case-studies?secret={SECRET}")
        
        if now.hour == 3 and now.minute == 0:
            await call_agent(f"/api/agent/generate-testimonials?secret={SECRET}")
        
        if now.hour == 4 and now.minute == 0:
            await call_agent(f"/api/agent/enhance-integrations?secret={SECRET}&count=5")
        
        if now.hour == 5 and now.minute == 0:
            await call_agent(f"/api/agent/enhance-faqs?secret={SECRET}&count=10")
        
        if now.hour in [6, 10, 14, 18] and now.minute == 0:
            await call_agent(f"/api/agent/daily-blog?secret={SECRET}&count=4")
        
        if now.hour in [20, 23] and now.minute == 0:
            await call_agent(f"/api/agent/daily-news?secret={SECRET}&count=4")
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(main())
```

Run with: `python scheduler.py &`

## Content Generation Summary

### Daily Output (24 hours):
- **Blog Posts**: 16 new posts (4 per batch × 4 batches)
- **News Articles**: 8 new articles (4 per batch × 2 batches)
- **Case Studies**: 3 new case studies
- **Testimonials**: 5 new testimonials
- **Enhanced Integrations**: 5 integrations get use cases
- **Enhanced FAQs**: 10 integrations get additional FAQs

### Monthly Output (30 days):
- **Blog Posts**: ~480 new posts
- **News Articles**: ~240 new articles
- **Case Studies**: ~90 case studies
- **Testimonials**: ~150 testimonials
- **Enhanced Integrations**: 150 integrations with use cases
- **Enhanced FAQs**: 300 integrations with extra FAQs

## Cost Analysis

### Gemini API (Free Tier):
- **Free tier limit**: 15 requests per minute, 1,500 requests per day
- **Our usage**: ~50 requests per day
- **Cost**: $0 (within free tier)

### Total Monthly Cost: $0

## Database Tables Created

1. `case_studies` - Stores AI-generated case studies
2. `testimonials` - Stores AI-generated testimonials
3. Integration enhancements:
   - `use_cases` column added to `integrations` table
   - `faq_7`, `faq_8` columns added to `integrations` table

## Monitoring

Check agent status:
```bash
# View recent blog posts
curl "https://integration-directory.com/api/health"

# Manual trigger (for testing)
curl "https://integration-directory.com/api/agent/daily-blog?secret=YOUR_SECRET&count=1"
```

## Notes

- All agents use Gemini 2.5 Flash (free tier)
- Rate limiting prevents API quota exhaustion
- Content is cached in database to avoid regeneration
- Newsletter sent only for first blog post per batch (not 4x)
- All content includes author attribution: "Vangari Sai Sampath"

## AdSense Compliance

This automation ensures:
- ✅ Consistent content publishing (16 blog posts/day)
- ✅ Fresh, unique content on all pages
- ✅ Social proof (case studies, testimonials)
- ✅ No "AI-generated" disclaimers
- ✅ Professional author attribution
- ✅ 300+ words per page minimum
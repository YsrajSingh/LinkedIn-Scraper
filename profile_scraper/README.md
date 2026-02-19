# LinkedIn User Profile Scraper

Scrapes public LinkedIn user profile data by handle or URL. Uses the same config pattern as the company scraper (User-Agent, sequential requests, delay).

## Setup

```bash
# From project root
cd ..
source venv/bin/activate  # or create venv: python3 -m venv venv && pip install scrapy
cd profile_scraper
```

## Configuration

Edit `profile_scraper/spiders/user_profile_scraper.py` and add usernames or full URLs to `desired_profiles`:

```python
desired_profiles = [
    "satya-nadella",
    "reidhoffman",
]
```

## Usage

```bash
scrapy crawl user_profile_scraper -O user_profiles.json
```

Output is saved to `user_profiles.json`.

## Output Fields

- `profile_url` - LinkedIn profile URL
- `name` - Full name
- `headline` - Job title / headline
- `location` - Location
- `profile_photo_url` - Profile picture URL
- `connections` - Connection count text
- `about` - About / summary section
- `current_role` - First experience/role

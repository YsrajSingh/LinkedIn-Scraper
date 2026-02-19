"""
Runs Scrapy spiders as subprocesses and returns scraped data.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Project root (parent of api/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _scrapy_cmd() -> list[str]:
    """Return command to run scrapy (uses same Python as API process)."""
    return [sys.executable, "-m", "scrapy"]


async def run_company_scraper(companies: list[str]) -> list[dict]:
    """Run company profile scraper for given company names. Returns list of company dicts."""
    if not companies:
        return []
    companies_arg = ",".join(c.strip() for c in companies if c.strip())
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name
    try:
        company_dir = PROJECT_ROOT / "company_data_scraper"
        proc = await asyncio.create_subprocess_exec(
            *_scrapy_cmd(),
            "crawl",
            "company_profile_scraper",
            "-a",
            f"companies={companies_arg}",
            "-O",
            output_path,
            cwd=str(company_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if not os.path.exists(output_path):
            if proc.returncode != 0 and stderr:
                raise RuntimeError(f"Scraper failed: {stderr.decode()}")
            return []
        with open(output_path) as f:
            content = f.read()
        if not content.strip():
            return []
        data = json.loads(content)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError as e:
        # Empty or invalid JSON (e.g. no items found)
        return []
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Company scraper failed: {e}") from e
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
    return []


async def run_profile_scraper(profiles: list[str]) -> list[dict]:
    """Run user profile scraper for given usernames/URLs. Returns list of profile dicts."""
    if not profiles:
        return []
    profiles_arg = ",".join(p.strip() for p in profiles if p.strip())
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_path = f.name
    try:
        profile_dir = PROJECT_ROOT / "profile_scraper"
        proc = await asyncio.create_subprocess_exec(
            *_scrapy_cmd(),
            "crawl",
            "user_profile_scraper",
            "-a",
            f"profiles={profiles_arg}",
            "-O",
            output_path,
            cwd=str(profile_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if not os.path.exists(output_path):
            if proc.returncode != 0 and stderr:
                raise RuntimeError(f"Scraper failed: {stderr.decode()}")
            return []
        with open(output_path) as f:
            content = f.read()
        if not content.strip():
            return []
        data = json.loads(content)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        # Empty or invalid JSON (e.g. no items found / all blocked)
        return []
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Profile scraper failed: {e}") from e
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
    return []

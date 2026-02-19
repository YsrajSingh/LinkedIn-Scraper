"""
Scrapes LinkedIn data using direct HTTP requests.
Works both locally and on serverless platforms (Vercel, etc.) —
no subprocess or Scrapy CLI needed.
"""

import re
import html as html_module
import time
from urllib.parse import quote_plus

import requests
from parsel import Selector

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_TIMEOUT = 20


# ────────────────────────────────────────────
#  Company scraper (LinkedIn returns 200 for /company/ pages)
# ────────────────────────────────────────────

def _normalize_company_url(handle_or_url: str) -> str:
    s = handle_or_url.strip().lower()
    if s.startswith("http"):
        return s
    if "linkedin.com/company/" in s:
        handle = s.split("linkedin.com/company/")[-1].split("?")[0].strip("/")
    else:
        handle = s.replace("linkedin.com/company/", "").strip("/")
    return f"https://www.linkedin.com/company/{handle}"


def _scrape_single_company(url: str) -> dict:
    """Fetch and parse a single LinkedIn company page."""
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    sel = Selector(text=resp.text)

    item = {}

    item["company_name"] = (
        sel.css(".top-card-layout__entity-info h1::text").get(default="not-found") or "not-found"
    ).strip()

    followers_text = sel.xpath(
        '//h3[contains(@class, "top-card-layout__first-subline")]/span/following-sibling::text()'
    ).get()
    try:
        item["linkedin_followers_count"] = int(
            (followers_text or "").split()[0].strip().replace(",", "")
        )
    except (ValueError, IndexError, AttributeError):
        item["linkedin_followers_count"] = 0

    item["company_logo_url"] = sel.css(
        "div.top-card-layout__entity-image-container img::attr(data-delayed-url)"
    ).get("not-found")

    item["about_us"] = sel.css(
        ".core-section-container__content p::text"
    ).get(default="not-found").strip()

    # Employee count
    try:
        emp_raw = sel.css("a.face-pile__cta::text").get(default="not-found").strip()
        nums = re.findall(r"\d{1,3}(?:,\d{3})*", emp_raw)
        if nums:
            item["num_of_employees"] = int(nums[0].replace(",", ""))
        else:
            item["num_of_employees"] = emp_raw
    except Exception:
        item["num_of_employees"] = "not-found"

    # Company details section
    try:
        details = sel.css(".core-section-container__content .mb-2")

        item["website"] = details[0].css("a::text").get(default="not-found").strip()

        industry_line = details[1].css(".text-md::text").getall()
        item["industry"] = industry_line[1].strip()

        size_line = details[2].css(".text-md::text").getall()
        item["company_size_approx"] = size_line[1].strip().split()[0]

        hq = details[3].css(".text-md::text").getall()
        if hq[0].lower().strip() == "headquarters":
            item["headquarters"] = hq[1].strip()
        else:
            item["headquarters"] = "not-found"

        comp_type = details[4].css(".text-md::text").getall()
        item["type"] = comp_type[1].strip()

        unsure = details[5].css(".text-md::text").getall()
        key = unsure[0].lower().strip()
        item[key] = unsure[1].strip()
        if key == "founded":
            specs = details[6].css(".text-md::text").getall()
            if specs[0].lower().strip() == "specialties":
                item["specialties"] = specs[1].strip()
            else:
                item["specialties"] = "not-found"
        elif key != "specialties":
            item["founded"] = "not-found"
            item["specialties"] = "not-found"

        # Funding
        item["funding"] = sel.css("p.text-display-lg::text").get(default="not-found").strip()
        rounds_raw = sel.xpath(
            '//section[contains(@class, "aside-section-container")]/div'
            '/a[contains(@class, "link-styled")]'
            '//span[contains(@class, "before:middot")]/text()'
        ).get() or ""
        try:
            item["funding_total_rounds"] = int(str(rounds_raw).strip().split()[0].replace(",", ""))
        except (ValueError, IndexError):
            item["funding_total_rounds"] = 0
        item["funding_option"] = sel.xpath(
            '//section[contains(@class, "aside-section-container")]/div'
            '//div[contains(@class, "my-2")]'
            '/a[contains(@class, "link-styled")]/text()'
        ).get("not-found").strip()
        item["last_funding_round"] = sel.xpath(
            '//section[contains(@class, "aside-section-container")]/div'
            '//div[contains(@class, "my-2")]'
            '/a[contains(@class, "link-styled")]'
            '//time[contains(@class, "before:middot")]/text()'
        ).get("not-found").strip()
    except IndexError:
        pass  # some details missing — keep what we have

    return item


async def run_company_scraper(companies: list[str]) -> list[dict]:
    """Scrape company profiles from LinkedIn. Returns list of company dicts."""
    if not companies:
        return []
    results = []
    for handle in companies:
        handle = handle.strip()
        if not handle:
            continue
        url = _normalize_company_url(handle)
        try:
            item = _scrape_single_company(url)
            results.append(item)
        except Exception as e:
            results.append({"company_name": handle, "error": str(e)})
    return results


# ────────────────────────────────────────────
#  Profile scraper
#  LinkedIn returns 999 for /in/ — uses li_at cookie or DDG fallback
# ────────────────────────────────────────────

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


def _extract_handle(profile_input: str) -> str:
    profile_input = profile_input.strip().rstrip("/")
    if "linkedin.com/in/" in profile_input:
        return profile_input.split("linkedin.com/in/")[-1].split("?")[0].strip("/")
    return profile_input


def _empty_profile(handle: str) -> dict:
    return {
        "profile_url": f"https://www.linkedin.com/in/{handle}",
        "name": "not-found",
        "headline": "not-found",
        "location": "not-found",
        "profile_photo_url": "not-found",
        "connections": "not-found",
        "about": "not-found",
        "current_role": "not-found",
    }


def _scrape_profile_authenticated(handle: str, li_at: str) -> dict:
    """Scrape LinkedIn profile using li_at session cookie.

    LinkedIn's authenticated pages embed profile data as JSON inside <code>
    tags (React SPA). We extract from that JSON.
    Returns None if the cookie is expired/invalid so the caller can fallback.
    """
    url = f"https://www.linkedin.com/in/{handle}"
    cookies = {"li_at": li_at}
    try:
        resp = requests.get(
            url, headers=HEADERS, cookies=cookies,
            timeout=REQUEST_TIMEOUT, allow_redirects=False,
        )
    except requests.exceptions.TooManyRedirects:
        return None  # cookie expired → redirect loop

    # 302 to same URL = cookie invalid/expired
    if resp.status_code in (302, 303, 301):
        return None

    if resp.status_code == 999:
        return None  # signal to fallback

    if resp.status_code != 200:
        return None

    item = _empty_profile(handle)
    item["profile_url"] = url

    # LinkedIn authenticated pages store profile data as JSON in <code> tags.
    # Extract miniProfile objects from the JSON.
    import json as _json
    code_blocks = re.findall(r"<code[^>]*>(.*?)</code>", resp.text, re.DOTALL)
    for block in code_blocks:
        decoded = (
            block.replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
        try:
            data = _json.loads(decoded)
        except (_json.JSONDecodeError, ValueError):
            continue

        for inc in data.get("included", []):
            if not isinstance(inc, dict):
                continue
            # Find the viewed profile's miniProfile (not the logged-in user)
            pid = inc.get("publicIdentifier", "")
            fname = inc.get("firstName", "")
            if fname and pid and pid.lower() == handle.lower():
                item["name"] = f"{fname} {inc.get('lastName', '')}".strip()
                item["headline"] = inc.get("occupation", "not-found")
                # Photo
                pic = inc.get("picture", {}) or {}
                root_url = pic.get("rootUrl", "")
                for art in pic.get("artifacts", []):
                    seg = art.get("fileIdentifyingUrlPathSegment", "")
                    if "200_200" in seg or "400_400" in seg:
                        item["profile_photo_url"] = f"{root_url}{seg}"
                        break

            # Location data
            if "geoLocationName" in inc and inc.get("publicIdentifier", "").lower() == handle.lower():
                item["location"] = inc.get("geoLocationName", "not-found")

        # Also look for summary/about in profile data
        for inc in data.get("included", []):
            if not isinstance(inc, dict):
                continue
            summary = inc.get("summary", "")
            if summary and handle.lower() in str(inc.get("publicIdentifier", "")).lower():
                item["about"] = summary

    # If we got a name, the extraction worked
    if item["name"] != "not-found":
        return item

    # Fallback: try CSS selectors (works for unauthenticated public profiles)
    sel = Selector(text=resp.text)

    name = (
        sel.css(".top-card-layout__entity-info h1::text").get()
        or sel.css("h1.text-heading-xlarge::text").get()
        or sel.xpath("//h1//text()").get()
    )
    if name and name.strip() not in ("", "Join LinkedIn", "Sign Up"):
        item["name"] = name.strip()

        headline = sel.css(".top-card-layout__headline::text").get()
        item["headline"] = headline.strip() if headline else item["headline"]

        location = sel.css(".top-card__subline-item::text").get()
        item["location"] = location.strip() if location else item["location"]

        item["profile_photo_url"] = (
            sel.css("img[data-delayed-url]::attr(data-delayed-url)").get()
            or sel.css(".top-card-layout__entity-image-container img::attr(src)").get()
            or item["profile_photo_url"]
        )

        about = sel.css(".core-section-container__content p::text").get()
        item["about"] = about.strip() if about else item["about"]

    return item


def _scrape_profile_ddg(handle: str) -> dict:
    """Scrape profile data from DuckDuckGo search results (fallback)."""
    item = _empty_profile(handle)
    query = quote_plus(f"site:linkedin.com/in/{handle}")
    try:
        resp = requests.get(
            f"{DDG_HTML_URL}?q={query}", headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
    except Exception:
        return item

    sel = Selector(text=resp.text)
    results = sel.css("div.result") or sel.css("div.results_links")

    best = None
    for r in results:
        url_text = (
            r.css("a.result__url::text").get("") or r.css("a.result__a::attr(href)").get("")
        ).strip()
        if handle.lower() in url_text.lower():
            best = r
            break
    if best is None and results:
        best = results[0]
    if best is None:
        return item

    raw_title = best.css("a.result__a").get("")
    raw_title = re.sub(r"<[^>]+>", "", raw_title).strip()
    raw_title = html_module.unescape(raw_title)
    raw_title = re.sub(r"\s*[-|]\s*LinkedIn\s*$", "", raw_title, flags=re.IGNORECASE)

    parts = re.split(r"\s+-\s+", raw_title, maxsplit=1)
    if len(parts) == 2:
        item["name"] = parts[0].strip()
        item["headline"] = parts[1].strip()
    elif raw_title:
        item["name"] = raw_title.strip()

    raw_snippet = best.css("a.result__snippet").get("")
    raw_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
    raw_snippet = html_module.unescape(raw_snippet)
    if raw_snippet:
        snippet_parts = raw_snippet.split(" · ", maxsplit=1)
        if len(snippet_parts) == 2:
            item["about"] = snippet_parts[1].strip()
            if item["headline"] == "not-found":
                item["headline"] = snippet_parts[0].strip()
        else:
            item["about"] = raw_snippet.strip()

    href = best.css("a.result__a::attr(href)").get("")
    if "linkedin.com/in/" in href:
        item["profile_url"] = href.split("?")[0]
    else:
        url_text = best.css("a.result__url::text").get("").strip()
        if "linkedin.com/in/" in url_text:
            if not url_text.startswith("http"):
                url_text = "https://" + url_text
            item["profile_url"] = url_text.split("?")[0]

    return item


async def run_profile_scraper(profiles: list[str], li_at: str = None) -> list[dict]:
    """Scrape user profiles. Uses li_at cookie if provided, else DDG fallback."""
    if not profiles:
        return []
    results = []
    for i, raw in enumerate(profiles):
        handle = _extract_handle(raw.strip())
        if not handle:
            continue

        item = None
        if li_at:
            try:
                item = _scrape_profile_authenticated(handle, li_at)
            except Exception:
                item = None  # fallback to DDG

        # Fallback to DDG if no cookie, or cookie failed (returned None)
        if item is None:
            item = _scrape_profile_ddg(handle)

        results.append(item)

        # Rate-limit between requests
        if i < len(profiles) - 1:
            time.sleep(2)

    return results

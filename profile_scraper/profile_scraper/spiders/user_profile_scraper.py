"""
LinkedIn User Profile Scraper

Scrapes public LinkedIn user profile data in real-time.

LinkedIn blocks unauthenticated access to /in/ pages (HTTP 999).
Two modes:
  1. Authenticated (recommended): pass your li_at cookie for full profile data.
     Usage: scrapy crawl user_profile_scraper -a profiles=user1,user2 -a li_at=YOUR_COOKIE
  2. Fallback: uses DuckDuckGo search results (name, headline, about only).
"""

import re
import html as html_module
from urllib.parse import quote_plus

import scrapy

DEFAULT_PROFILES = ["satya-nadella", "reidhoffman"]

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


def extract_handle(profile_input: str) -> str:
    """Extract LinkedIn handle from username or URL."""
    profile_input = profile_input.strip().rstrip("/")
    if "linkedin.com/in/" in profile_input:
        return profile_input.split("linkedin.com/in/")[-1].split("?")[0].strip("/")
    return profile_input


def normalize_profile_url(handle: str) -> str:
    """Build full LinkedIn profile URL from handle."""
    return f"https://www.linkedin.com/in/{handle}"


class UserProfileScraperSpider(scrapy.Spider):
    name = "user_profile_scraper"

    handle_httpstatus_list = [999]

    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
    }

    def __init__(self, profiles: str = None, li_at: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raw_list = [p.strip() for p in (profiles or "").split(",") if p.strip()]
        if not raw_list:
            raw_list = DEFAULT_PROFILES
        self.handles = [extract_handle(p) for p in raw_list]
        self.li_at = li_at.strip() if li_at else None
        if not self.handles:
            raise ValueError("No profile handles provided. Use -a profiles=user1,user2")
        if self.li_at:
            self.logger.info("Using authenticated mode (li_at cookie provided)")
        else:
            self.logger.info("No li_at cookie — falling back to DuckDuckGo search mode")

    def start_requests(self):
        for index, handle in enumerate(self.handles):
            if self.li_at:
                # Authenticated: hit LinkedIn directly
                yield scrapy.Request(
                    url=normalize_profile_url(handle),
                    callback=self.parse_linkedin_profile,
                    cookies={"li_at": self.li_at},
                    meta={"handle": handle, "profile_index": index},
                    dont_filter=True,
                )
            else:
                # Fallback: use DuckDuckGo search
                query = quote_plus(f"site:linkedin.com/in/{handle}")
                yield scrapy.Request(
                    url=f"{DDG_HTML_URL}?q={query}",
                    callback=self.parse_ddg_results,
                    meta={"handle": handle, "profile_index": index},
                    dont_filter=True,
                )

    # ── Authenticated mode: parse LinkedIn profile page directly ──

    def parse_linkedin_profile(self, response):
        handle = response.meta["handle"]
        profile_index = response.meta["profile_index"]
        self.logger.info(
            f"Scraping profile {profile_index + 1}/{len(self.handles)} "
            f"[{handle}] | Status: {response.status}"
        )

        if response.status == 999:
            self.logger.warning(
                f"LinkedIn returned 999 for {handle}. Cookie may be expired. "
                "Falling back to DuckDuckGo search."
            )
            query = quote_plus(f"site:linkedin.com/in/{handle}")
            yield scrapy.Request(
                url=f"{DDG_HTML_URL}?q={query}",
                callback=self.parse_ddg_results,
                meta={"handle": handle, "profile_index": profile_index},
                dont_filter=True,
            )
            return

        item = self._empty_item(handle)

        # Name
        item["name"] = (
            response.css(".top-card-layout__entity-info h1::text").get()
            or response.css("h1.text-heading-xlarge::text").get()
            or response.css("h1.inline::text").get()
            or response.xpath("//h1//text()").get()
        )
        item["name"] = item["name"].strip() if item["name"] else "not-found"

        # Headline
        item["headline"] = (
            response.css(".top-card-layout__headline::text").get()
            or response.css("div.text-body-medium::text").get()
            or response.xpath("//div[contains(@class, 'headline')]//text()").get()
        )
        item["headline"] = item["headline"].strip() if item["headline"] else "not-found"

        # Location
        item["location"] = (
            response.css(".top-card__subline-item::text").get()
            or response.css("div.text-body-small.inline::text").get()
            or response.xpath("//span[contains(@class, 'text-body-small')]//text()").get()
        )
        item["location"] = item["location"].strip() if item["location"] else "not-found"

        # Profile photo
        item["profile_photo_url"] = (
            response.css("img[data-delayed-url]::attr(data-delayed-url)").get()
            or response.css(".top-card-layout__entity-image-container img::attr(src)").get()
            or response.css(".pv-top-card-profile-picture img::attr(src)").get()
            or "not-found"
        )

        # Connections
        conn_text = (
            response.css("a.face-pile__cta::text").get()
            or response.xpath("//span[contains(text(), 'connection')]/text()").get()
        )
        item["connections"] = conn_text.strip() if conn_text else "not-found"

        # About
        about = (
            response.css(".core-section-container__content p::text").get()
            or response.css("section#about p::text").get()
            or response.css(".pv-about__summary-text::text").get()
        )
        item["about"] = about.strip() if about else "not-found"

        # Current role
        try:
            exp = (
                response.css("section#experience li span[aria-hidden=true]::text").get()
                or response.css("[data-section='experience'] .experience-item__title::text").get()
            )
            item["current_role"] = exp.strip() if exp else "not-found"
        except (IndexError, TypeError):
            item["current_role"] = "not-found"

        yield item

    # ── Fallback mode: parse DuckDuckGo search results ──

    def parse_ddg_results(self, response):
        handle = response.meta["handle"]
        profile_index = response.meta["profile_index"]
        self.logger.info(
            f"[DDG fallback] profile {profile_index + 1}/{len(self.handles)} "
            f"[{handle}] | Status: {response.status}"
        )

        item = self._empty_item(handle)

        # DDG HTML results: <div class="result"> or older formats
        results = response.css("div.result") or response.css("div.results_links")

        # Find result matching our handle
        best = None
        for r in results:
            url_text = (r.css("a.result__url::text").get("") or
                        r.css("a.result__a::attr(href)").get("")).strip()
            if handle.lower() in url_text.lower():
                best = r
                break
        if best is None and results:
            best = results[0]

        if best is None:
            self.logger.warning(f"No DDG results for {handle}")
            yield item
            return

        # Parse title: "Full Name - Headline | LinkedIn"
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

        # Parse snippet (contains about/summary)
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

        # Extract LinkedIn URL from result
        href = best.css("a.result__a::attr(href)").get("")
        if "linkedin.com/in/" in href:
            item["profile_url"] = href.split("?")[0]
        else:
            url_text = best.css("a.result__url::text").get("").strip()
            if "linkedin.com/in/" in url_text:
                if not url_text.startswith("http"):
                    url_text = "https://" + url_text
                item["profile_url"] = url_text.split("?")[0]

        yield item

    # ── Helpers ──

    def _empty_item(self, handle: str) -> dict:
        return {
            "profile_url": normalize_profile_url(handle),
            "name": "not-found",
            "headline": "not-found",
            "location": "not-found",
            "profile_photo_url": "not-found",
            "connections": "not-found",
            "about": "not-found",
            "current_role": "not-found",
        }

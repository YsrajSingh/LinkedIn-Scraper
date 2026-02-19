"""
LinkedIn User Profile Scraper

Scrapes public LinkedIn user profile data. Add profile URLs or usernames to
desired_profiles below, then run:
    scrapy crawl user_profile_scraper -O user_profiles.json
"""

import re
import scrapy


DEFAULT_PROFILES = ["satya-nadella", "reidhoffman"]


def normalize_profile_url(profile_input: str) -> str:
    """Convert username or URL to full LinkedIn profile URL."""
    profile_input = profile_input.strip()
    if profile_input.startswith("http"):
        return profile_input
    # Remove leading/trailing slashes and linkedin.com prefix if partial
    username = profile_input.replace("linkedin.com/in/", "").strip("/")
    return f"https://www.linkedin.com/in/{username}"


class UserProfileScraperSpider(scrapy.Spider):
    name = "user_profile_scraper"

    def __init__(self, profiles: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile_list = [p.strip() for p in (profiles or "").split(",") if p.strip()]
        if not profile_list:
            profile_list = DEFAULT_PROFILES
        self.profile_urls = [normalize_profile_url(p) for p in profile_list]
        if not self.profile_urls:
            raise ValueError("No profile URLs to scrape. Add usernames via -a profiles=user1,user2")

    def start_requests(self):
        for i, url in enumerate(self.profile_urls):
            yield scrapy.Request(
                url=url,
                callback=self.parse_profile,
                meta={"profile_index": i},
            )

    def parse_profile(self, response):
        profile_index = response.meta["profile_index"]
        print("********")
        print(f"Scraping profile {profile_index + 1} of {len(self.profile_urls)}")
        print("********")

        item = {}

        # Profile URL
        item["profile_url"] = response.url

        # Name - try multiple selectors (LinkedIn uses similar structure to company pages)
        item["name"] = (
            response.css(".top-card-layout__entity-info h1::text").get()
            or response.css("h1.text-heading-xlarge::text").get()
            or response.css("h1.inline::text").get()
            or response.xpath("//h1//text()").get()
        )
        if item["name"]:
            item["name"] = item["name"].strip()
        else:
            item["name"] = "not-found"

        # Headline / job title
        item["headline"] = (
            response.css(".top-card-layout__entity-info .top-card-layout__headline::text").get()
            or response.css("div.text-body-medium::text").get()
            or response.xpath("//div[contains(@class, 'headline')]//text()").get()
        )
        if item["headline"]:
            item["headline"] = item["headline"].strip()
        else:
            item["headline"] = "not-found"

        # Location
        item["location"] = (
            response.css(".top-card-layout__entity-info .top-card__subline-item::text").get()
            or response.css("div.text-body-small.inline::text").get()
            or response.xpath("//span[contains(@class, 'text-body-small')]//text()").get()
        )
        if item["location"]:
            item["location"] = item["location"].strip()
        else:
            item["location"] = "not-found"

        # Profile photo
        item["profile_photo_url"] = (
            response.css("img[data-delayed-url]::attr(data-delayed-url)").get()
            or response.css("div.top-card-layout__entity-image-container img::attr(src)").get()
            or response.css(".pv-top-card-profile-picture img::attr(src)").get()
            or "not-found"
        )

        # Connection count (e.g. "500+ connections")
        conn_text = (
            response.css("a.face-pile__cta::text").get()
            or response.xpath("//span[contains(text(), 'connection')]/text()").get()
            or "not-found"
        )
        if conn_text and conn_text != "not-found":
            item["connections"] = conn_text.strip()
        else:
            item["connections"] = "not-found"

        # About / Summary
        item["about"] = (
            response.css(".core-section-container__content p::text").get()
            or response.css("section#about p::text").get()
            or response.css(".pv-about__summary-text::text").get()
            or "not-found"
        )
        if item["about"]:
            item["about"] = item["about"].strip()
        else:
            item["about"] = "not-found"

        # Experience - get first role title from experience section
        try:
            exp_title = (
                response.css("section#experience li span[aria-hidden=true]::text").get()
                or response.css("[data-section='experience'] .experience-item__title::text").get()
                or "not-found"
            )
            item["current_role"] = exp_title.strip() if exp_title else "not-found"
        except (IndexError, TypeError):
            item["current_role"] = "not-found"

        yield item

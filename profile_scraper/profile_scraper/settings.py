BOT_NAME = "profile_scraper"

SPIDER_MODULES = ["profile_scraper.spiders"]
NEWSPIDER_MODULE = "profile_scraper.spiders"

# Desktop Chrome User-Agent (LinkedIn is less aggressive blocking desktop browsers)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

ROBOTSTXT_OBEY = False

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Delay between profile requests (LinkedIn rate-limits /in/ pages more than /company/)
DOWNLOAD_DELAY = 5

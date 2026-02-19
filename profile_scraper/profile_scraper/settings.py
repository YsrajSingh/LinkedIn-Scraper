BOT_NAME = "profile_scraper"

SPIDER_MODULES = ["profile_scraper.spiders"]
NEWSPIDER_MODULE = "profile_scraper.spiders"

# Same User-Agent as company scraper (which successfully returns 200)
USER_AGENT = "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"

ROBOTSTXT_OBEY = False

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Delay between profile requests (LinkedIn rate-limits /in/ pages more than /company/)
DOWNLOAD_DELAY = 5

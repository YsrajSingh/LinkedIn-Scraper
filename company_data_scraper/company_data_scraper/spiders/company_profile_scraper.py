import re
import scrapy


DEFAULT_COMPANIES = ["openai", "microsoft"]


def normalize_company_url(handle_or_url: str) -> str:
    """Convert company handle or full URL to LinkedIn company page URL."""
    s = handle_or_url.strip().lower()
    if s.startswith("http"):
        return s
    # Extract handle from partial URLs like "linkedin.com/company/microsoft"
    if "linkedin.com/company/" in s:
        handle = s.split("linkedin.com/company/")[-1].split("?")[0].strip("/")
    else:
        handle = s.replace("linkedin.com/company/", "").strip("/")
    return f"https://www.linkedin.com/company/{handle}"


class CompanyProfileScraperSpider(scrapy.Spider):
    name = "company_profile_scraper"

    def __init__(self, companies: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        handles = [c.strip() for c in (companies or "").split(",") if c.strip()]
        if not handles:
            handles = DEFAULT_COMPANIES
        self.company_pages = list({normalize_company_url(h) for h in handles})
        if not self.company_pages:
            raise ValueError("No company handles provided. Use -a companies=handle1,handle2")

    def start_requests(self):
        company_index_tracker = 0

        first_url = self.company_pages[company_index_tracker]
        yield scrapy.Request(url=first_url, callback=self.parse_response,
                             meta={'company_index_tracker': company_index_tracker})

    def parse_response(self, response):
        company_index_tracker = response.meta['company_index_tracker']
        print('********')
        print(
            f'Scraping page: {str(company_index_tracker + 1)} of {str(len(self.company_pages))}')
        print('********')

        company_item = {}

        company_item['company_name'] = (response.css('.top-card-layout__entity-info h1::text').get(
            default='not-found') or 'not-found').strip()

        followers_text = response.xpath(
            '//h3[contains(@class, "top-card-layout__first-subline")]/span/following-sibling::text()').get()
        try:
            company_item['linkedin_followers_count'] = int(
                (followers_text or '').split()[0].strip().replace(',', ''))
        except (ValueError, IndexError, AttributeError):
            company_item['linkedin_followers_count'] = 0
        # attr(src) didn't work, I saw the img element response and found out `src` has changed to `data-delayed-url` for which there was logo link.
        company_item['company_logo_url'] = response.css(
            'div.top-card-layout__entity-image-container img::attr(data-delayed-url)').get('not-found')

        company_item['about_us'] = response.css('.core-section-container__content p::text').get(
            default='not-found').strip()

        try:
            followers_num_match = re.findall(r'\d{1,3}(?:,\d{3})*',
                                             response.css('a.face-pile__cta::text').get(default='not-found').strip())
            if followers_num_match:
                company_item['num_of_employees'] = int(
                    followers_num_match[0].replace(',', ''))
            else:
                company_item['num_of_employees'] = response.css('a.face-pile__cta::text').get(
                    default='not-found').strip()
        except Exception as e:
            print("Error occurred while getting number of employees: {e}")

        try:
            company_details = response.css(
                '.core-section-container__content .mb-2')

            company_item['website'] = company_details[0].css(
                'a::text').get(default='not-found').strip()

            company_industry_line = company_details[1].css(
                '.text-md::text').getall()
            company_item['industry'] = company_industry_line[1].strip()

            company_size_line = company_details[2].css(
                '.text-md::text').getall()
            company_item['company_size_approx'] = company_size_line[1].strip().split()[
                0]

            company_headquarters = company_details[3].css(
                '.text-md::text').getall()
            if company_headquarters[0].lower().strip() == 'headquarters':
                company_item['headquarters'] = company_headquarters[1].strip()
            else:
                company_item['headquarters'] = 'not-found'

            company_type = company_details[4].css('.text-md::text').getall()
            company_item['type'] = company_type[1].strip()

            # specialities or founded, one among them -> storing in `unsure_parameter`
            unsure_parameter = company_details[5].css(
                '.text-md::text').getall()
            unsure_parameter_key = unsure_parameter[0].lower().strip()
            company_item[unsure_parameter_key] = unsure_parameter[1].strip()
            # `founded` comes before specialties if exists, or else `specialties` at first means that `founded` parameter isn't defined
            if unsure_parameter_key == 'founded':
                company_specialties = company_details[6].css(
                    '.text-md::text').getall()
                # after `founded` is extracted, check if `specialties` is defined
                if company_specialties[0].lower().strip() == 'specialties':
                    company_item['specialties'] = company_specialties[1].strip()
                else:
                    company_item['specialties'] = 'not-found'
            elif unsure_parameter_key != 'specialties' or unsure_parameter_key == 'founded':
                company_item['founded'] = 'not-found'
                company_item['specialties'] = 'not-found'

            # funding parameters, more feasible error handling to be implemented, if sir needs to have..
            company_item['funding'] = response.css(
                'p.text-display-lg::text').get(default='not-found').strip()
            funding_rounds_raw = response.xpath(
                '//section[contains(@class, "aside-section-container")]/div/a[contains(@class, "link-styled")]//span[contains(@class, "before:middot")]/text()').get() or ''
            try:
                company_item['funding_total_rounds'] = int(str(funding_rounds_raw).strip().split()[0].replace(',', ''))
            except (ValueError, IndexError, AttributeError):
                company_item['funding_total_rounds'] = 0
            company_item['funding_option'] = response.xpath(
                '//section[contains(@class, "aside-section-container")]/div//div[contains(@class, "my-2")]/a[contains(@class, "link-styled")]/text()').get(
                'not-found').strip()
            company_item['last_funding_round'] = response.xpath(
                '//section[contains(@class, "aside-section-container")]/div//div[contains(@class, "my-2")]/a[contains(@class, "link-styled")]//time[contains(@class, "before:middot")]/text()').get(
                'not-found').strip()

        except IndexError:
            print("Error: *****Skipped index, as some details are missing*********")

        yield company_item

        company_index_tracker += 1

        if (company_index_tracker <= len(self.company_pages) - 1):
            next_url = self.company_pages[company_index_tracker]
            yield scrapy.Request(url=next_url, callback=self.parse_response,
                                 meta={'company_index_tracker': company_index_tracker})

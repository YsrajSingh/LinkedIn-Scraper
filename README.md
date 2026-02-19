# LinkedIn Scraper

A comprehensive LinkedIn data scraping system that extracts company and profile information via CLI and REST API. Combines company directory scraping, company profile scraping, and user profile scraping into one tool.

## Table of Contents

1. [Features](#1-features)
2. [Installation](#2-installation)
3. [API Usage](#3-api-usage)
4. [CLI Usage](#4-cli-usage-scrapers)
5. [Data Output](#5-data-output)
6. [Contributing](#6-contributing)
7. [Credits](#7-credits)

## 1. Features

- **Scalability**: Extract thousands of company profiles without being blocked by LinkedIn.
- **Customizable**: Define your own data collection parameters and filters.
- **Data Output**: Export data in a structured JSON format for easy integration into your workflows.
- **Comprehensive**: Gather company names, associated URLs, and detailed company profile information

- **User-Agent Rotation**: Automatically rotate user agents to avoid detection and blocking by LinkedIn.
- **Crawler Control**: Customize crawling speed and frequency to avoid overloading LinkedIn's servers.
- **Data Analysis**: Perform data analysis, visualization, and other research activities to gain insights into the LinkedIn company profiles you have scraped.

## 2. Installation

To set up the LinkedIn Scraper, follow these steps:

```bash
# 1. Clone the repository
git clone https://github.com/YsrajSingh/LinkedIn-Scraper.git
cd LinkedIn-Scraper

# 3. (Recommended) Create a virtual environment
python3 -m venv venv

# 4. Activate the virutal environment
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# 5. Install required packages
pip install -r requirements.txt
```

## 3. API Usage

The project includes a FastAPI service to search companies and profiles via HTTP.

### Start the API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs for interactive API documentation.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/company` | Search multiple companies |
| POST | `/profile` | Search multiple profiles |

**Example - Search companies (by handle or URL):**
```bash
curl -X POST http://localhost:8000/company \
  -H "Content-Type: application/json" \
  -d '{"companies": ["microsoft", "tutorflo", "openai"]}'
```

**Example - Search profiles:**
```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{"profiles": ["satya-nadella", "reidhoffman"]}'
```
*Profile scraping uses the same setup as company scraping. Success may vary by network; try a different connection if requests fail.*

## 4. CLI Usage (Scrapers)

### LinkedIn Company Directory Scraper

1. To run the LinkedIn Company Directory Scraper, first navigate to the `company_data_scraper` directory:
```bash
cd company_data_scraper
```
2. Then run the script to store all the possible company names and their linkedin page URLs:
```bash
scrapy crawl linkedin_directory_scraper -O directory_data.json
```

The scraped company directory data will be stored in the `directory_data.json` file in a structured JSON format or use `directory_data.csv`, according to your convinience.

### LinkedIn Company Profile Scraper

Scrapes company data directly from LinkedIn using company handles (e.g. `microsoft`, `tutorflo`) or full URLs. No directory file required.

```bash
cd company_data_scraper
scrapy crawl company_profile_scraper -a "companies=microsoft,tutorflo,openai" -O company_profile_data.json
```

### LinkedIn User Profile Scraper

```bash
cd profile_scraper
scrapy crawl user_profile_scraper -a "profiles=satya-nadella,reidhoffman" -O user_profiles.json
```

## 5. Data Output

### LinkedIn Company Directory Scraper Output

The extracted directory data will be structured as follows:

```json
[
  {
    "company_name_1": "url of the company",
    "company_name_2": "url of the company",
    ...
  }
]
```
The Project is capable of extracting ~ 2 Lakh company names along with their linkedin page URLs from the Linkedin Company Directory.

### LinkedIn Company Profile Scraper Output

The extracted company profile data will include details such as company name, LinkedIn followers count, company logo URL, about us section, number of employees, website, industry, company size, headquarters, type, founding year, specialties, funding details, and last funding round information.

Below is an example of the output format of the company profile scraper with 16 useful and distinct parameters.

```json
[
    {
        "company_name": "OpenAI",
        "linkedin_followers_count": 2610704,
        "company_logo_url": "https://media.licdn.com/dms/image/C4E0BAQG0lRhNgYJCXw/company-logo_200_200/0/1678382029586?e=2147483647&v=beta&t=ixFAwvTgLyU99x2ihJEGBuy0T-Mp6lenxo_fDUJP3vY",
        "about_us": "OpenAI is an AI research and deployment company dedicated to ensuring that general-purpose artificial intelligence benefits all of humanity. AI is an extremely powerful tool that must be created with safety and human needs at its core. OpenAI is dedicated to putting that alignment of interests first — ahead of profit.\n\nTo achieve our mission, we must encompass and value the many different perspectives, voices, and experiences that form the full spectrum of humanity. Our investment in diversity, equity, and inclusion is ongoing, executed through a wide range of initiatives, and championed and supported by leadership.\n\nAt OpenAI, we believe artificial intelligence has the potential to help people solve immense global challenges, and we want the upside of AI to be widely shared. Join us in shaping the future of technology.",
        "num_of_employees": 1230,
        "website": "https://openai.com/",
        "industry": "Research Services",
        "company_size_approx": "201-500",
        "headquarters": "San Francisco, CA",
        "type": "Partnership",
        "founded": "2015",
        "specialties": "artificial intelligence and machine learning",
        "funding": "not-found",
        "funding_total_rounds": 10,
        "funding_option": "Secondary market",
        "last_funding_round": "Sep 14, 2023"
    }
]

```

## 6. Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/YsrajSingh/LinkedIn-Scraper).

## 7. Credits

This project extends the [LinkedIn Company Data Scraping System](https://github.com/KarthikDani/LinkedIn-Company-Data-Scraping-System) by KarthikDani. The original company directory and profile scrapers provided the foundation for this extended version, which adds user profile scraping and a FastAPI interface.

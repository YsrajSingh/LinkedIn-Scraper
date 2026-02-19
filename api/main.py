"""
LinkedIn Scraping API

FastAPI service exposing company and profile scrapers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import company, profile

app = FastAPI(
    title="LinkedIn Scraping API",
    description="Search for company and profile data from LinkedIn",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router, prefix="/company", tags=["company"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])


@app.get("/")
def root():
    return {
        "message": "LinkedIn Scraping API",
        "docs": "/docs",
        "endpoints": {
            "company": "POST /company - Search multiple companies",
            "profile": "POST /profile - Search multiple profiles",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}

"""
Company search API - POST /company
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.scraper_runner import run_company_scraper

router = APIRouter()


class CompanyRequest(BaseModel):
    companies: list[str] = Field(
        ...,
        description="List of company handles or URLs (e.g. ['microsoft', 'tutorflo', 'openai'])",
        min_length=1,
        max_length=50,
    )


class CompanyResponse(BaseModel):
    success: bool = True
    count: int
    data: list[dict]


@router.post("", response_model=CompanyResponse)
async def search_companies(request: CompanyRequest):
    """
    Search for multiple companies by handle or URL. Scrapes directly from LinkedIn.
    Examples: microsoft, tutorflo, openai, or full https://linkedin.com/company/... URLs.
    """
    try:
        data = await run_company_scraper(request.companies)
        return CompanyResponse(success=True, count=len(data), data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

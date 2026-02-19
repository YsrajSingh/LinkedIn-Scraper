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
        description="List of company names to search (e.g. ['Microsoft', 'OpenAI'])",
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
    Search for multiple companies. Returns LinkedIn company profile data.
    Companies must exist in the directory (directorydata.json).
    """
    try:
        data = await run_company_scraper(request.companies)
        return CompanyResponse(success=True, count=len(data), data=data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

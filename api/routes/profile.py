"""
Profile search API - POST /profile
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.scraper_runner import run_profile_scraper

router = APIRouter()


class ProfileRequest(BaseModel):
    profiles: list[str] = Field(
        ...,
        description="List of profile usernames or URLs (e.g. ['satya-nadella', 'reidhoffman'])",
        min_length=1,
        max_length=50,
    )
    li_at: str | None = Field(
        default=None,
        description=(
            "LinkedIn session cookie (li_at) for authenticated scraping. "
            "Without it, falls back to search-engine results (limited fields). "
            "Get it from browser DevTools > Application > Cookies > linkedin.com > li_at"
        ),
    )


class ProfileResponse(BaseModel):
    success: bool = True
    count: int
    data: list[dict]


@router.post("", response_model=ProfileResponse)
async def search_profiles(request: ProfileRequest):
    """
    Search for multiple LinkedIn profiles. Accepts usernames (e.g. satya-nadella)
    or full profile URLs.

    For best results, provide your LinkedIn li_at cookie for authenticated access.
    Without it, the scraper falls back to search-engine results with limited data.
    """
    try:
        data = await run_profile_scraper(request.profiles, li_at=request.li_at)
        return ProfileResponse(success=True, count=len(data), data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

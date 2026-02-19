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


class ProfileResponse(BaseModel):
    success: bool = True
    count: int
    data: list[dict]


@router.post("", response_model=ProfileResponse)
async def search_profiles(request: ProfileRequest):
    """
    Search for multiple LinkedIn profiles. Accepts usernames (e.g. satya-nadella)
    or full profile URLs.
    """
    try:
        data = await run_profile_scraper(request.profiles)
        return ProfileResponse(success=True, count=len(data), data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

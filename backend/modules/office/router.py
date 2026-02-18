"""Office module API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

from .models import OfficeResponse
from .service import office_service

router = APIRouter()


@router.get("/", response_model=OfficeResponse)
async def get_office(db: AsyncSession = Depends(get_db)):
    """Get the office view with agent workstations."""
    return await office_service.get_office(db)

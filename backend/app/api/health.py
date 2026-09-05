from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.schemas import HealthOut
from app.providers import get_provider

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthOut)
async def health(db: AsyncSession = Depends(get_db)):
    postgres_ok = False
    pgvector_ok = False
    try:
        await db.execute(text("SELECT 1"))
        postgres_ok = True
        result = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        pgvector_ok = result.scalar_one_or_none() is not None
    except Exception:
        pass

    try:
        ollama_ok = await get_provider("ollama").health_check()
    except Exception:
        ollama_ok = False

    return HealthOut(
        api=True,
        postgres=postgres_ok,
        pgvector=pgvector_ok,
        ollama=ollama_ok,
        configured_provider=settings.default_llm_provider,
    )

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        from app.models import db_models  # noqa
        await conn.run_sync(Base.metadata.create_all)
        await conn.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_hnsw_idx
            ON transcript_chunks USING hnsw (embedding vector_cosine_ops)
            """
        )

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

def get_normalized_database_url_and_args(raw_url: str):
    """
    Normalizes database URL for SQLAlchemy + asyncpg, specifically handling:
    - postgres:// -> postgresql+asyncpg://
    - postgresql:// -> postgresql+asyncpg://
    - Supabase/PgBouncer poolers (port 6543 or statement_cache_size=0)
    - SSL mode stripping from query string to connect_args
    """
    url = raw_url.strip()

    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    connect_args = {}

    # Check if host is remote (not localhost) or explicitly Supabase
    parsed = urlparse(url)
    is_remote = parsed.hostname not in ("localhost", "127.0.0.1", "postgres", None)
    is_supabase = "supabase" in (parsed.hostname or "")

    # Clean query parameters: asyncpg does not accept 'sslmode' in query params
    if parsed.query:
        query_dict = parse_qs(parsed.query)
        if "sslmode" in query_dict:
            del query_dict["sslmode"]
            # Reconstruct URL without sslmode
            new_query = urlencode(query_dict, doseq=True)
            url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))

    if is_remote:
        # Require SSL for cloud hosts like Supabase, Neon, AWS RDS
        connect_args["ssl"] = "require"

    if is_supabase or parsed.port == 6543:
        # Supabase transaction pooler requires statement_cache_size = 0
        connect_args["statement_cache_size"] = 0

    return url, connect_args


database_url, asyncpg_connect_args = get_normalized_database_url_and_args(settings.DATABASE_URL)

engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    connect_args=asyncpg_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

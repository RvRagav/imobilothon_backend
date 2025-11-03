import asyncio
import traceback
from app.db import models  # ensure models are imported so Base knows about them
from app.core.config import DATABASE_URL
from app.db import database

"""
Create database tables. This script supports either a synchronous SQLAlchemy
Engine or an AsyncEngine exposed as `engine` in `app.db.database`.

It will detect the engine type and run the appropriate create_all path.
"""

try:
    # Import AsyncEngine for isinstance check
    from sqlalchemy.ext.asyncio import AsyncEngine
except Exception:
    AsyncEngine = None


def create_tables_sync(engine):
    from sqlalchemy import inspect, text
    try:
        print(f"Using sync DATABASE_URL={DATABASE_URL}")

        # Try to ensure PostGIS exists (non-fatal)
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
        except Exception:
            print("Note: could not ensure PostGIS extension (may require superuser). Continuing...")

        models.Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Tables present in database:")
        for t in tables:
            print(f" - {t}")

        print("✅ Tables created/verified successfully")
    except Exception:
        print("❌ Failed to create tables (sync)")
        traceback.print_exc()


async def create_tables_async(aengine):
    try:
        print(f"Using async DATABASE_URL={DATABASE_URL}")
        async with aengine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        print("✅ Tables created/verified successfully (async)")
    except Exception:
        print("❌ Failed to create tables (async)")
        traceback.print_exc()


if __name__ == "__main__":
    eng = getattr(database, "engine", None)
    if eng is None:
        print("No engine found in app.db.database")
    else:
        # If AsyncEngine is available and engine is instance, run async path
        if AsyncEngine is not None and isinstance(eng, AsyncEngine):
            asyncio.run(create_tables_async(eng))
        else:
            # Assume sync Engine
            create_tables_sync(eng)

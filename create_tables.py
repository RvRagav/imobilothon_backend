import asyncio
from app.db.database import engine
from app.db import models  # ✅ important: import your models so Base knows about them

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    print("✅ Tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_models())

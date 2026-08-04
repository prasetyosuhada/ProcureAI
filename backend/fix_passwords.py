import asyncio
from app.core.database import get_db_session, engine
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import update

async def main():
    async for session in get_db_session():
        hashed = get_password_hash("password123")
        await session.execute(update(User).values(hashed_password=hashed))
        await session.commit()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

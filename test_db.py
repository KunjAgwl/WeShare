import asyncio
from app.config.database import Database

async def test_db():
    print("Initializing DB...")
    db = Database()
    await db.init_db()
    print("Registering user...")
    ok = await db.register_user("testuser", "password123", "Test User")
    print(f"Registration success: {ok}")
    db.client.close()

if __name__ == "__main__":
    asyncio.run(test_db())

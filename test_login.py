import asyncio
from app.config.database import Database

async def test_db():
    print("Initializing DB...")
    db = Database()
    await db._ensure_ready()
    
    print("Fetching users:")
    res = await db.execute("SELECT username, password_hash, display_name FROM users")
    for r in res.rows:
        print(f" -> {r}")
        
    print("Testing login with 'testuser' and 'password123':")
    login = await db.login_user("testuser", "password123")
    print(f"Login result: {login}")

if __name__ == "__main__":
    asyncio.run(test_db())

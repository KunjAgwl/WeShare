import asyncio
from app.config.database import Database

async def test_db():
    print("Initializing DB...")
    db = Database()
    await db._ensure_ready()
    
    print("Sending file message...")
    try:
        await db.send_message("test", "test", "demo", is_file=True)
        print("Success!")
    except Exception as e:
        print(f"ERROR: {e}")
        
if __name__ == "__main__":
    asyncio.run(test_db())

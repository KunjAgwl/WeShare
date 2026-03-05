import os
import hashlib
import libsql_client
from dotenv import load_dotenv

load_dotenv()

TURSO_URL = os.getenv("TURSO_DATABASE_URL", "")
if TURSO_URL.startswith("libsql://"):
    TURSO_URL = TURSO_URL.replace("libsql://", "https://", 1)
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


import asyncio

class Database:
    def __init__(self):
        self.client = libsql_client.create_client_sync(
            url=TURSO_URL,
            auth_token=TURSO_AUTH_TOKEN,
        )
        self._ready = False

    async def execute(self, stmt, args=()):
        # Run synchronous HTTP execute in a thread to keep the asyncio event loop unblocked
        return await asyncio.to_thread(self.client.execute, stmt, args)

    async def _ensure_ready(self):
        if not self._ready:
            await self.init_db()

    # ── Schema ──
    async def init_db(self):
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                owner TEXT NOT NULL,
                contact_username TEXT NOT NULL,
                PRIMARY KEY (owner, contact_username)
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                content TEXT NOT NULL,
                is_file BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._ready = True

    # ── Auth ──
    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    async def register_user(self, username: str, password: str, display_name: str) -> bool:
        await self._ensure_ready()
        existing = await self.execute(
            "SELECT username FROM users WHERE username = ?", [username])
        if existing.rows:
            return False
        await self.execute(
            "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
            [username, self._hash(password), display_name],
        )
        return True

    async def login_user(self, username: str, password: str):
        await self._ensure_ready()
        result = await self.execute(
            "SELECT username, display_name FROM users WHERE username = ? AND password_hash = ?",
            [username, self._hash(password)],
        )
        return result.rows[0] if result.rows else None

    async def update_display_name(self, username: str, display_name: str):
        await self.execute(
            "UPDATE users SET display_name = ? WHERE username = ?",
            [display_name, username],
        )

    async def update_last_seen(self, username: str):
        await self.execute(
            "UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE username = ?",
            [username],
        )

    async def get_user(self, username: str):
        result = await self.execute(
            "SELECT username, display_name FROM users WHERE username = ?", [username])
        return result.rows[0] if result.rows else None

    # ── Contacts ──
    async def add_contact(self, owner: str, contact_username: str) -> bool:
        user = await self.get_user(contact_username)
        if not user:
            return False
        try:
            await self.execute(
                "INSERT OR IGNORE INTO contacts (owner, contact_username) VALUES (?, ?)",
                [owner, contact_username],
            )
            return True
        except Exception:
            return False

    async def get_contacts(self, owner: str):
        result = await self.execute(
            "SELECT c.contact_username, u.display_name FROM contacts c "
            "JOIN users u ON c.contact_username = u.username WHERE c.owner = ?",
            [owner],
        )
        return result.rows

    # ── Messages ──
    async def send_message(self, sender, receiver, content, is_file=False):
        await self.execute(
            "INSERT INTO messages (sender, receiver, content, is_file) VALUES (?, ?, ?, ?)",
            [sender, receiver, content, is_file],
        )

    async def get_messages(self, user1, user2):
        result = await self.execute(
            "SELECT sender, content, is_file, timestamp FROM messages "
            "WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) "
            "ORDER BY timestamp ASC",
            [user1, user2, user2, user1],
        )
        return result.rows

    def close(self):
        self.client.close()

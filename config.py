import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0") or "0")
BOT_NAME = os.getenv("BOT_NAME", "BELLAMY").strip()
PORT = int(os.getenv("PORT", "8080") or "8080")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")

OFFICIAL_CHANNEL_ID = os.getenv("OFFICIAL_CHANNEL_ID", "").strip()
OFFICIAL_CHANNEL_LINK = os.getenv("OFFICIAL_CHANNEL_LINK", "").strip()
OFFICIAL_GROUP_ID = os.getenv("OFFICIAL_GROUP_ID", "").strip()
OFFICIAL_GROUP_LINK = os.getenv("OFFICIAL_GROUP_LINK", "").strip()

_db = os.getenv("DATABASE_URL", "").strip()
if _db.startswith("postgres://"):
    _db = _db.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db.startswith("postgresql://") and "+asyncpg" not in _db:
    _db = _db.replace("postgresql://", "postgresql+asyncpg://", 1)
DATABASE_URL = _db

# Preenchidos em runtime (main.py) após resolução via get_chat
CHANNEL_NUMERIC_ID: int | None = None
GROUP_NUMERIC_ID: int | None = None

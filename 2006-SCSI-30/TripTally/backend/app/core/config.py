import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv, find_dotenv

# Load .env from the project root
env_path = find_dotenv(usecwd=True)
if not env_path:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
else:
    load_dotenv(env_path)


# Your database and auth settings
class Settings(BaseSettings):
    DATABASE_URL: str ="REDACTED_DATABASE_URL"

    SECRET_KEY: str = "REDACTED_SECRET_KEY"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_IOS_CLIENT_ID: str = ""

    model_config = ConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Allow extra fields in .env without validation errors
    )

settings = Settings()

# Teammate's Google Maps API config
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_SERVER_API_KEY")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

if not GOOGLE_MAPS_API_KEY:
    here = os.getcwd()
    raise RuntimeError(
        "Google API key missing. Looked for GOOGLE_MAPS_API_KEY or GOOGLE_SERVER_API_KEY.\n"
        f"CWD={here}\n"
        f".env searched at: {env_path}"
    )

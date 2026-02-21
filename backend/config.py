from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path

import os
import secrets

BASE_DIR = Path(__file__).resolve().parent

# Load backend/.env first, then fall back to repository-root .env.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

@dataclass
class AuthConfig:
    database_url: str = os.getenv("DATABASE_URL")
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    min_password_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

config = AuthConfig()

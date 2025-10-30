from dotenv import load_dotenv
from dataclasses import dataclass

import os
import secrets

load_dotenv()

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

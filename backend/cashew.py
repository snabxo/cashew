from datetime import datetime, timedelta
from typing import Optional
import re

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from backend.config import config
from backend.database import get_db
from backend.models import UserDB, RefreshTokenDB, LoginAttemptDB


# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < config.min_password_length:
            raise ValueError(f'Password must be at least {config.min_password_length} characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    token_type: Optional[str] = None


class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.access_token_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[config.algorithm])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return TokenData(username=username, token_type=token_type)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Auth Service Functions
def check_account_lockout(db: Session, user: UserDB) -> bool:
    if not user.login_attempts:
        return False

    attempt = user.login_attempts[0]
    if attempt.locked_until and datetime.utcnow() < attempt.locked_until:
        return True

    if attempt.locked_until and datetime.utcnow() >= attempt.locked_until:
        attempt.attempt_count = 0
        attempt.locked_until = None
        db.commit()

    return False


def record_failed_login(db: Session, user: UserDB):
    if not user.login_attempts:
        attempt = LoginAttemptDB(user_id=user.id, attempt_count=1, last_attempt=datetime.utcnow())
        db.add(attempt)
    else:
        attempt = user.login_attempts[0]
        attempt.attempt_count += 1
        attempt.last_attempt = datetime.utcnow()

        if attempt.attempt_count >= config.max_login_attempts:
            attempt.locked_until = datetime.utcnow() + timedelta(minutes=config.lockout_duration_minutes)

    db.commit()


def reset_login_attempts(db: Session, user: UserDB):
    if user.login_attempts:
        attempt = user.login_attempts[0]
        attempt.attempt_count = 0
        attempt.locked_until = None
        db.commit()


def store_refresh_token(db: Session, token: str, user_id: int):
    expires_at = datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
    db_token = RefreshTokenDB(token=token, user_id=user_id, expires_at=expires_at)
    db.add(db_token)
    db.commit()


def validate_refresh_token(db: Session, token: str) -> Optional[UserDB]:
    db_token = db.query(RefreshTokenDB).filter(RefreshTokenDB.token == token).first()
    if not db_token or datetime.utcnow() > db_token.expires_at:
        if db_token:
            db.delete(db_token)
            db.commit()
        return None
    return db_token.user


def revoke_refresh_token(db: Session, token: str):
    db_token = db.query(RefreshTokenDB).filter(RefreshTokenDB.token == token).first()
    if db_token:
        db.delete(db_token)
        db.commit()


def cleanup_expired_tokens(db: Session):
    db.query(RefreshTokenDB).filter(RefreshTokenDB.expires_at < datetime.utcnow()).delete()
    db.commit()


# Dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                           db: Session = Depends(get_db)) -> User:
    token_data = decode_token(credentials.credentials)
    if token_data.token_type != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = db.query(UserDB).filter(UserDB.username == token_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return User.from_orm(user)


# FastAPI App
app = FastAPI(title="Production-Ready Authentication Service using Python with Postgres and Alembic")


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter(UserDB.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(UserDB).filter(UserDB.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    db_user = UserDB(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User.from_orm(db_user)


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == user_data.username).first()

    if user and check_account_lockout(db, user):
        raise HTTPException(status_code=429,
                            detail=f"Account locked. Try again in {config.lockout_duration_minutes} minutes.")

    if not user or not verify_password(user_data.password, user.hashed_password):
        if user:
            record_failed_login(db, user)
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    reset_login_attempts(db, user)
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    store_refresh_token(db, refresh_token, user.id)
    cleanup_expired_tokens(db)

    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    user = validate_refresh_token(db, refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    try:
        token_data = decode_token(refresh_token)
        if token_data.token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except HTTPException:
        revoke_refresh_token(db, refresh_token)
        raise

    if not user.is_active:
        revoke_refresh_token(db, refresh_token)
        raise HTTPException(status_code=401, detail="User inactive")

    new_access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    revoke_refresh_token(db, refresh_token)
    store_refresh_token(db, new_refresh_token, user.id)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@app.post("/logout")
async def logout(refresh_token: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    revoke_refresh_token(db, refresh_token)
    return {"message": "Successfully logged out"}


@app.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {"status": "healthy" if db_status == "healthy" else "degraded", "database": db_status,
            "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# Cashew

A production-ready authentication service built with FastAPI, PostgreSQL, SQLAlchemy, and Alembic. Provides secure user registration, login, token management, and account protection features.

## Features

### Security
- **Password Hashing**: BCrypt algorithm with automatic salting
- **JWT Tokens**: Access tokens (30 min) and refresh tokens (7 days)
- **Brute Force Protection**: Account lockout after 5 failed login attempts
- **Password Validation**: Enforces strong password requirements
- **Token Revocation**: Logout functionality with refresh token blacklisting

### Database
- **PostgreSQL**: Production-grade relational database
- **SQLAlchemy ORM**: Type-safe database operations
- **Alembic Migrations**: Version-controlled schema management
- **Connection Pooling**: Optimized database connections
- **Foreign Key Constraints**: Data integrity with cascade deletes

### API Features
- **RESTful Design**: Clean, intuitive API endpoints
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`
- **Health Check**: Database connectivity monitoring
- **Error Handling**: Comprehensive validation and error responses

## Project Structure

```
cashew/
├── README.md
├── LICENSE.md
├── requirements.txt
├── .env.example
├── config.py              # Configuration management
├── database.py            # Database connection and session
├── models.py              # SQLAlchemy database models
├── cashew.py        # Main FastAPI application
├── alembic.ini            # Alembic configuration
└── alembic/
    ├── env.py             # Alembic environment setup
    ├── script.py.mako     # Migration template
    └── versions/          # Migration files
```

## Prerequisites

- Python 3.8+
- Docker (for Postgres)
- pip 

## Installation

### 1. Clone the Repository

```bash
git clone <https://github.com/belikesnab/cashew.git>
cd cashew
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
alembic==1.13.1
annotated-doc==0.0.3
annotated-types==0.7.0
anyio==4.11.0
bcrypt==5.0.0
cffi==2.0.0
click==8.1.8
cryptography==46.0.3
dnspython==2.7.0
ecdsa==0.19.1
email-validator==2.3.0
exceptiongroup==1.3.0
fastapi==0.120.3
h11==0.16.0
idna==3.11
Mako==1.3.10
MarkupSafe==3.0.3
passlib==1.7.4
psycopg2-binary==2.9.11
pyasn1==0.6.1
pycparser==2.23
pydantic==2.12.3
pydantic_core==2.41.4
python-dotenv==1.2.1
python-jose==3.5.0
python-multipart==0.0.20
rsa==4.9.1
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.44
starlette==0.49.1
tomli==2.3.0
typing-inspection==0.4.2
typing_extensions==4.15.0
uliweb-alembic==0.6.9
uvicorn==0.38.0
```

### 4. Set Up PostgreSQL

```bash
# Start postgres docker container
# Make sure docker is already running
docker-compose up -d

# Connect to postgres
docker exec -it cashew-db bash
psql -U postgres
CREATE DATABASE auth_db;
\q
```

### 5. Configure Environment Variables

Create `.env` file:

```bash
# username and password should match the ones in docker compose
DATABASE_URL=postgresql://username:password@localhost:5432/cashew_db
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

**.env.example:**
```
DATABASE_URL="postgresql://postgres:cashewdevpass123@localhost:5432/cashew_db"
SECRET_KEY="change-this-to-a-secure-random-string"
```

### 6. Initialize Database with Alembic

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 7. Run the Service

```bash
# Development
python cashew.py

# Production with Uvicorn
uvicorn cashew:app --host 0.0.0.0 --port 8000 --workers 4

# With auto-reload for development
uvicorn cashew:app --reload
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### 1. Register User
**POST** `/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Username Requirements:**
- 3-50 characters
- Only letters, numbers, hyphens, and underscores

---

#### 2. Login
**POST** `/login`

Authenticate user and receive tokens.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401`: Incorrect username or password
- `429`: Account locked (after 5 failed attempts)
- `400`: Inactive user

---

#### 3. Refresh Token
**POST** `/refresh`

Get new access token using refresh token.

**Query Parameters:**
- `refresh_token`: The refresh token received from login

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### 4. Logout
**POST** `/logout`

Revoke refresh token and logout user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `refresh_token`: The refresh token to revoke

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

#### 5. Get Current User
**GET** `/me`

Get information about the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00"
}
```

---

#### 6. Health Check
**GET** `/health`

Check service and database health.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2025-01-15T10:30:00"
}
```

## Usage Examples

### Python with requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/login", json={
    "username": "john_doe",
    "password": "SecurePass123!"
})
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Get current user
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/me", headers=headers)
print(response.json())

# Refresh token
response = requests.post(
    f"{BASE_URL}/refresh",
    params={"refresh_token": refresh_token}
)
new_tokens = response.json()

# Logout
response = requests.post(
    f"{BASE_URL}/logout",
    headers=headers,
    params={"refresh_token": refresh_token}
)
print(response.json())
```

### cURL

```bash
# Register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"SecurePass123!"}'

# Get current user
curl -X GET http://localhost:8000/me \
  -H "Authorization: Bearer <access_token>"

# Refresh token
curl -X POST "http://localhost:8000/refresh?refresh_token=<refresh_token>"

# Logout
curl -X POST "http://localhost:8000/logout?refresh_token=<refresh_token>" \
  -H "Authorization: Bearer <access_token>"
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000';

// Register
const register = async () => {
  const response = await fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'john_doe',
      email: 'john@example.com',
      password: 'SecurePass123!'
    })
  });
  return await response.json();
};

// Login
const login = async () => {
  const response = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'john_doe',
      password: 'SecurePass123!'
    })
  });
  return await response.json();
};

// Get current user
const getCurrentUser = async (accessToken: string) => {
  const response = await fetch(`${BASE_URL}/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return await response.json();
};
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Refresh Tokens Table
```sql
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```

### Login Attempts Table
```sql
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    attempt_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP
);
```

## Database Migrations

### Create a New Migration

```bash
# After modifying models.py
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>
```

### Rollback Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Downgrade to base (empty database)
alembic downgrade base
```

### Migration History

```bash
# Show current version
alembic current

# Show migration history
alembic history --verbose

# Show pending migrations
alembic heads
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/auth_db` | Yes |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Auto-generated | Yes (production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` | No |
| `MIN_PASSWORD_LENGTH` | Minimum password length | `8` | No |
| `MAX_LOGIN_ATTEMPTS` | Failed attempts before lockout | `5` | No |
| `LOCKOUT_DURATION_MINUTES` | Account lockout duration | `15` | No |

### Modifying Configuration

Edit `config.py`:

```python
@dataclass
class AuthConfig:
    database_url: str = os.getenv("DATABASE_URL")
    secret_key: str = os.getenv("SECRET_KEY")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # ... other settings
```

## Testing

### Manual Testing with HTTPie

```bash
# Install HTTPie
pip install httpie

# Register
http POST localhost:8000/register \
  username=testuser \
  email=test@example.com \
  password=TestPass123!

# Login
http POST localhost:8000/login \
  username=testuser \
  password=TestPass123!

# Use token
http GET localhost:8000/me \
  Authorization:"Bearer <access_token>"
```

### Unit Tests (Example)

```python
# test_auth.py
import pytest
from fastapi.testclient import TestClient
from cashew import app

client = TestClient(app)

def test_register():
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_login():
    # First register
    client.post("/register", json={
        "username": "logintest",
        "email": "login@example.com",
        "password": "TestPass123!"
    })
    
    # Then login
    response = client.post("/login", json={
        "username": "logintest",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
```

## Deployment

### Docker

**Dockerfile:**
```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "cashew:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
services:
  cashew-db:
    image: postgres:18-alpine
    container_name: cashew-db
    platform: linux/arm64  # Optional: for Apple Silicon hosts
    environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: cashewdevpass123
        POSTGRES_DB: cashew_db
    volumes:
        - cashew-data:/var/lib/postgresql/data
    ports:
        - "5432:5432"

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:cashewdevpass123@localhost:5432/cashew_db
      SECRET_KEY: your-production-secret-key-here
    depends_on:
      - cashew-db
    command: >
      sh -c "alembic upgrade head &&
             uvicorn auth_service:app --host 0.0.0.0 --port 8000"

volumes:
  cashew-data:
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS/TLS
- [ ] Set up PostgreSQL with proper user permissions
- [ ] Configure connection pooling
- [ ] Enable CORS if needed
- [ ] Set up logging and monitoring
- [ ] Implement rate limiting middleware
- [ ] Configure backup strategy
- [ ] Use a reverse proxy (nginx/traefik)
- [ ] Set up health check monitoring
- [ ] Enable database SSL connections

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations

### Best Practices
- **Never commit** `.env` files or credentials to version control
- Use **environment variables** for all sensitive configuration
- Rotate **SECRET_KEY** periodically in production
- Enable **database SSL** connections
- Implement **rate limiting** to prevent abuse
- Use **HTTPS** in production
- Keep dependencies **updated** regularly
- Monitor for **suspicious activity**

### Password Security
- Passwords are hashed using BCrypt with automatic salting
- Plain text passwords are never stored
- Password strength requirements enforced

### Token Security
- JWT tokens signed with HS256 algorithm
- Access tokens have short expiration (30 minutes)
- Refresh tokens stored in database for revocation
- Token type validation prevents misuse

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps

# Test connection
docker exec -it cashew-db bash

# Check logs
docker logs cashew-db
```

### Migration Issues

```bash
# Reset database (WARNING: destroys data)
alembic downgrade base
alembic upgrade head

# Check current version
alembic current

# Manually create revision if autogenerate fails
alembic revision -m "Manual migration"
```

### Common Errors

**Error:** `ModuleNotFoundError: No module named 'config'`
- **Solution:** Ensure all files are in the same directory or adjust Python path

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`
- **Solution:** Check PostgreSQL is running and DATABASE_URL is correct

**Error:** `jose.exceptions.JWTError: Signature verification failed`
- **Solution:** SECRET_KEY has changed; users need to re-login

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and create migrations if needed
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
4. Commit your changes **including migration files**
   ```bash
   git add alembic/versions/*.py
   git commit -m 'Add amazing feature'
   ```
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
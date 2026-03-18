# CrashGuard API v2 — Setup Guide

## Project Structure
```
crashguard/
├── main.py                          # FastAPI entry point
├── requirements.txt
├── .env.example                     # Copy to .env and fill in values
│
└── app/
    ├── api/
    │   ├── auth_routes.py           # /auth/* endpoints
    │   └── analysis_routes.py       # /analysis/* endpoints
    │
    ├── core/
    │   ├── config.py                # Settings from .env
    │   ├── database.py              # MongoDB Atlas connection
    │   ├── security.py              # JWT + bcrypt
    │   └── dependencies.py          # get_current_user, get_verified_user
    │
    ├── models/
    │   └── schemas.py               # All Pydantic schemas
    │
    ├── services/
    │   ├── user_service.py          # User CRUD + auth
    │   ├── email_service.py         # OTP generation + Resend email
    │   ├── analysis_service.py      # Save/retrieve analyses per user
    │   ├── calculations.py          # (your original file)
    │   ├── risk_engine.py           # (your original file)
    │   └── recommendations.py       # (your original file)
    │
    └── utils/
        └── csv_validator.py         # (your original file)
```

---

## Quick Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. MongoDB Atlas
1. Create a free cluster at https://mongodb.com/atlas
2. Create a database user
3. Whitelist your IP (or 0.0.0.0/0 for dev)
4. Copy the connection string into `.env` as `MONGODB_URL`

### 4. Email (optional)
This project no longer uses email verification/OTP; users can register and log in without needing an email code.

### 5. Run
```bash
uvicorn main:app --reload
```

### 6. Interactive API docs
Open http://localhost:8000/docs

---

## API Flow

### Registration + Onboarding
```
POST /auth/register          → Creates account
POST /auth/login             → Returns access_token + refresh_token
POST /auth/onboarding/business-profile  → Saves business profile (Step 2)
```

### Using the API (authenticated)
```
GET  /auth/me                → Get current user profile
POST /analysis/analyze       → Run analysis + auto-save to history
POST /analysis/upload-csv    → CSV upload + run + save
GET  /analysis/history       → Get user's past analyses
GET  /analysis/{id}          → Get specific analysis
DELETE /analysis/{id}        → Delete analysis
```

### Token management
```
POST /auth/refresh           → Get new tokens (refresh token rotation)
POST /auth/logout            → Revoke current device
POST /auth/logout-all        → Revoke all devices
```

---

## MongoDB Collections

| Collection       | Purpose                              |
|-----------------|--------------------------------------|
| users           | User accounts + business profiles    |
| analyses        | Per-user analysis history            |
| refresh_tokens  | Active sessions per user             |

---

## Security Features
- **Bcrypt** password hashing
- **JWT** access tokens (60 min) + refresh tokens (30 days)
- **Refresh token rotation** — old token deleted on use
- **Per-user data isolation** — all analyses scoped to user_id
- **MongoDB TTL index** — OTPs auto-deleted after expiry

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


# ── Enums / Literals ─────────────────────────────────────────────────────────
RoleType = Literal["Founder", "Finance", "Operator", "Other"]
IndustryType = Literal["SaaS", "Ecommerce", "Agency", "Other"]
StageType = Literal["Startup", "Growth", "Mature"]


# ── Step 1: Account Creation ─────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: str = Field(..., min_length=7, max_length=20)
    role: RoleType

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Step 2: Business Profile ─────────────────────────────────────────────────
class BusinessProfileRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    industry_type: IndustryType
    business_stage: StageType
    number_of_employees: int = Field(..., ge=1)
    monthly_recurring_revenue: Optional[float] = None
    website: Optional[str] = None


# ── OTP ──────────────────────────────────────────────────────────────────────
class SendOTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


# ── Login ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Token Responses ──────────────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── User Response (safe — no password) ───────────────────────────────────────
class BusinessProfileResponse(BaseModel):
    company_name: Optional[str] = None
    industry_type: Optional[str] = None
    business_stage: Optional[str] = None
    number_of_employees: Optional[int] = None
    monthly_recurring_revenue: Optional[float] = None
    website: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone_number: str
    role: str
    is_email_verified: bool
    onboarding_complete: bool
    business_profile: Optional[BusinessProfileResponse] = None
    created_at: datetime


# ── Analysis ─────────────────────────────────────────────────────────────────
class CrashInput(BaseModel):
    revenue: List[float]
    expenses: List[float]
    cash_in_hand: float
    customers: List[int]


class AnalysisSaveRequest(BaseModel):
    """Frontend can pass a label to identify this analysis run."""
    label: Optional[str] = None
    input_data: CrashInput


class AnalysisResponse(BaseModel):
    id: str
    user_id: str
    label: Optional[str]
    result: dict
    created_at: datetime


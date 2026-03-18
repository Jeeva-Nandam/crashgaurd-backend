from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    BusinessProfileRequest,
)
from app.services import user_service
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, get_verified_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── 1. Register ───────────────────────────────────────────────────────────────
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    """
    Create a new account.
    """
    if await user_service.email_exists(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    await user_service.create_user(data)

    return {
        "message": "Account created successfully.",
        "email": data.email,
    }


# ── 4. Login ──────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """
    Login with email + password.
    Returns access token (short-lived) + refresh token (long-lived).
    """
    user = await user_service.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    access_token = create_access_token({"sub": user["id"]})
    refresh_token = create_refresh_token({"sub": user["id"]})

    await user_service.store_refresh_token(user["id"], refresh_token)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── 5. Refresh Token ──────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshTokenRequest):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    Old refresh token is deleted (rotation prevents reuse).
    """
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    user_id = await user_service.validate_and_rotate_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used.",
        )

    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})
    await user_service.store_refresh_token(user_id, new_refresh)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── 6. Logout ─────────────────────────────────────────────────────────────────
@router.post("/logout")
async def logout(
    data: RefreshTokenRequest,
    current_user: dict = Depends(get_current_user),
):
    """Revoke the provided refresh token (single device logout)."""
    await user_service.validate_and_rotate_refresh_token(data.refresh_token)
    return {"message": "Logged out successfully."}


@router.post("/logout-all")
async def logout_all(current_user: dict = Depends(get_current_user)):
    """Revoke all refresh tokens (all devices logout)."""
    await user_service.revoke_all_refresh_tokens(current_user["id"])
    return {"message": "Logged out from all devices."}


# ── 7. Get current user ───────────────────────────────────────────────────────
@router.get("/me")
async def get_me(current_user: dict = Depends(get_verified_user)):
    """Return the authenticated user's profile (no password hash)."""
    user = current_user.copy()
    user.pop("password_hash", None)
    return user


# ── 8. Business Profile (Onboarding Step 2) ───────────────────────────────────
@router.post("/onboarding/business-profile")
async def setup_business_profile(
    data: BusinessProfileRequest,
    current_user: dict = Depends(get_verified_user),
):
    """
    Step 2 of onboarding: save the business profile.
    Can be called again to update the profile later.
    """
    updated_user = await user_service.update_business_profile(current_user["id"], data)
    updated_user.pop("password_hash", None)
    return {
        "message": "Business profile saved successfully.",
        "user": updated_user,
    }

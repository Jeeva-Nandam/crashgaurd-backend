import random
import string
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.core.database import get_otp_collection
import httpx


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


async def send_otp_email(email: str, otp: str, full_name: str = "there") -> bool:
    """
    Send OTP via Resend (https://resend.com).
    Free tier: 100 emails/day, 3000/month — perfect for getting started.
    """
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color: #1a1a2e;">Verify your email</h2>
        <p>Hi {full_name},</p>
        <p>Your CrashGuard verification code is:</p>
        <div style="
            background: #f4f4f8;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 24px 0;
        ">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1a1a2e;">
                {otp}
            </span>
        </div>
        <p style="color: #666;">This code expires in <strong>{settings.OTP_EXPIRE_MINUTES} minutes</strong>.</p>
        <p style="color: #666; font-size: 12px;">
            If you didn't request this, please ignore this email.
        </p>
    </div>
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{settings.APP_NAME} <{settings.FROM_EMAIL}>",
                    "to": [email],
                    "subject": f"Your {settings.APP_NAME} verification code: {otp}",
                    "html": html_body,
                },
                timeout=10.0,
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Email send error: {e}")
        return False


async def store_otp(email: str, otp: str):
    """Store OTP in MongoDB with TTL expiry."""
    collection = get_otp_collection()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Upsert — replaces any existing OTP for this email
    await collection.replace_one(
        {"email": email},
        {
            "email": email,
            "otp": otp,
            "expires_at": expires_at,
            "verified": False,
            "attempts": 0,
        },
        upsert=True,
    )


async def verify_otp(email: str, otp: str) -> tuple[bool, str]:
    """
    Verify OTP. Returns (success, error_message).
    Increments attempt count and blocks after 5 failed tries.
    """
    collection = get_otp_collection()
    record = await collection.find_one({"email": email})

    if not record:
        return False, "No OTP found. Please request a new one."

    if record.get("verified"):
        return False, "OTP already used. Please request a new one."

    now = datetime.now(timezone.utc)
    expires_at = record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        await collection.delete_one({"email": email})
        return False, "OTP has expired. Please request a new one."

    if record.get("attempts", 0) >= 5:
        await collection.delete_one({"email": email})
        return False, "Too many failed attempts. Please request a new OTP."

    if record["otp"] != otp:
        await collection.update_one(
            {"email": email},
            {"$inc": {"attempts": 1}}
        )
        remaining = 5 - (record.get("attempts", 0) + 1)
        return False, f"Invalid OTP. {remaining} attempts remaining."

    # Mark as verified
    await collection.update_one({"email": email}, {"$set": {"verified": True}})
    return True, "OTP verified successfully."


async def delete_otp(email: str):
    """Clean up OTP after use."""
    collection = get_otp_collection()
    await collection.delete_one({"email": email})

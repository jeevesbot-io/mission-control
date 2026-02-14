from fastapi import Request
from itsdangerous import URLSafeTimedSerializer

from core.config import settings

serializer = URLSafeTimedSerializer(settings.session_secret)


async def get_current_user(request: Request) -> dict:
    """Extract user from Cloudflare Access email or return default when CF is disabled."""
    cf_email = getattr(request.state, "cf_user_email", None)
    if cf_email:
        return {"id": cf_email, "name": cf_email.split("@")[0]}
    return {"id": "default", "name": "Jeeves"}

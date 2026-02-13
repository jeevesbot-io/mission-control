from itsdangerous import URLSafeTimedSerializer

from core.config import settings

serializer = URLSafeTimedSerializer(settings.session_secret)


async def get_current_user() -> dict:
    """Stub auth — returns a default user. Real auth in Phase 2."""
    return {"id": "default", "name": "Jeeves"}

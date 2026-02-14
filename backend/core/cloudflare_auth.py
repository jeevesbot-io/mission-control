"""Cloudflare Access JWT validation middleware.

When cf_access_team is configured, validates the Cf-Access-Jwt-Assertion header
(or CF_Authorization cookie for WebSocket) against Cloudflare's JWKS endpoint.
When cf_access_team is empty (default), all requests pass through.
"""

import logging
import time

import httpx
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings

logger = logging.getLogger(__name__)

# JWKS cache
_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}
JWKS_CACHE_TTL = 300  # 5 minutes


async def _get_public_keys() -> list[jwt.algorithms.RSAAlgorithm]:
    """Fetch and cache Cloudflare Access public keys."""
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_CACHE_TTL:
        return _jwks_cache["keys"]

    certs_url = f"https://{settings.cf_access_team}.cloudflareaccess.com/cdn-cgi/access/certs"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(certs_url, timeout=10)
            resp.raise_for_status()
            jwks = resp.json()

        public_keys = []
        for key_data in jwks.get("keys", []):
            public_keys.append(
                jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
            )

        _jwks_cache["keys"] = public_keys
        _jwks_cache["fetched_at"] = now
        logger.info("Refreshed Cloudflare Access JWKS (%d keys)", len(public_keys))
        return public_keys
    except Exception:
        logger.exception("Failed to fetch Cloudflare Access JWKS")
        # Return stale cache if available
        return _jwks_cache["keys"]


async def validate_cf_token(token: str) -> str | None:
    """Validate a CF Access JWT and return the user email, or None on failure."""
    if not settings.cf_access_team or not settings.cf_access_audience:
        return None

    public_keys = await _get_public_keys()
    if not public_keys:
        logger.error("No Cloudflare Access public keys available")
        return None

    for key in public_keys:
        try:
            payload = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=settings.cf_access_audience,
            )
            return payload.get("email")
        except jwt.ExpiredSignatureError:
            logger.warning("CF Access token expired")
            return None
        except jwt.InvalidTokenError:
            continue

    logger.warning("CF Access token failed validation against all keys")
    return None


class CloudflareAccessMiddleware(BaseHTTPMiddleware):
    """Validate Cloudflare Access JWT on every request (when enabled)."""

    async def dispatch(self, request: Request, call_next):
        # Skip when CF Access is not configured
        if not settings.cf_access_team:
            request.state.cf_user_email = None
            return await call_next(request)

        # Always allow health check (Docker HEALTHCHECK needs it unauthenticated)
        if request.url.path == "/api/health":
            request.state.cf_user_email = None
            return await call_next(request)

        # Extract token from header or cookie
        token = request.headers.get("Cf-Access-Jwt-Assertion")
        if not token:
            token = request.cookies.get("CF_Authorization")

        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Cloudflare Access token"},
            )

        email = await validate_cf_token(token)
        if not email:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid Cloudflare Access token"},
            )

        request.state.cf_user_email = email
        return await call_next(request)

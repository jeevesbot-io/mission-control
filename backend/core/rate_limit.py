"""Rate limiting via slowapi — uses CF-Connecting-IP when behind Cloudflare."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _get_client_ip(request: Request) -> str:
    """Extract client IP: prefer CF-Connecting-IP, fall back to remote addr."""
    return (
        request.headers.get("CF-Connecting-IP")
        or get_remote_address(request)
    )


limiter = Limiter(key_func=_get_client_ip, default_limits=["60/minute"])

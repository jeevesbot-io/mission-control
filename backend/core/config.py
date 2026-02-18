from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "postgresql+asyncpg://jeeves@localhost:5432/jeeves"
    port: int = 5055
    debug: bool = False
    session_secret: str = "change-me"
    cors_origins: str = "http://localhost:5173,http://localhost:5055"
    memory_path: str = "~/.openclaw/workspace/memory"
    dashboard_data_dir: str = "~/.openclaw/workspace/dashboard/data"
    workspace_dir: str = "~/.openclaw/workspace"
    openclaw_dir: str = "~/.openclaw"
    sessions_dir: str = "~/.openclaw/agents/main/sessions"
    bundled_skills_dir: str = ""  # empty = disabled (Linux path doesn't exist on macOS)
    openclaw_url: str = "http://localhost:18789"
    openclaw_token: str = ""
    openclaw_gateway_url: str = "http://localhost:18789"
    openclaw_gateway_token: str = ""

    # Cloudflare Access (empty = disabled)
    cf_access_team: str = ""
    cf_access_audience: str = ""

    # Path to gog CLI binary (empty = calendar disabled)
    gog_path: str = "/opt/homebrew/bin/gog"

    @model_validator(mode="after")
    def _validate_production_secret(self):
        if not self.debug and "change" in self.session_secret.lower():
            raise ValueError(
                "SESSION_SECRET must be set to a secure value in production (DEBUG=false). "
                "Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def memory_dir(self) -> Path:
        return Path(self.memory_path).expanduser()

    @property
    def dashboard_data_path(self) -> Path:
        return Path(self.dashboard_data_dir).expanduser()

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_dir).expanduser()

    @property
    def openclaw_path(self) -> Path:
        return Path(self.openclaw_dir).expanduser()

    @property
    def sessions_path(self) -> Path:
        return Path(self.sessions_dir).expanduser()


settings = Settings()

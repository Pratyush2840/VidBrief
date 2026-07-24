from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    cors_origins: str = "http://localhost:5173"
    rate_limit: str = "5/minute"
    cache_ttl_seconds: int = 86400
    cache_max_size: int = 500

    # Optional: routes youtube-transcript-api requests through a Webshare
    # proxy. Needed on cloud hosts (Render/Railway/etc.) since YouTube blocks
    # datacenter IPs; not needed for local dev. Get credentials at webshare.io.
    webshare_proxy_username: str = ""
    webshare_proxy_password: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

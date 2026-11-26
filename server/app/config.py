"""Settings of the API process, from environment variables."""
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Where the rasters are, the public URL base of the app, and the app version."""
    rain_dir: Path
    public_base: str
    app_version: str


def settings_from_env() -> Settings:
    """RAIN_DIR (default /data/rain), PUBLIC_BASE (default /, always ends with /), APP_VERSION."""
    base = os.environ.get("PUBLIC_BASE", "/")
    if not base.endswith("/"):
        base += "/"
    return Settings(
        rain_dir=Path(os.environ.get("RAIN_DIR", "/data/rain")),
        public_base=base,
        app_version=os.environ.get("APP_VERSION", "1.1.0"),
    )

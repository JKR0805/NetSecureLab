from pathlib import Path
from typing import Dict, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCANS_DIR_DEFAULT = BASE_DIR / "scans"
REPORTS_DIR_DEFAULT = BASE_DIR / "reports"

class Settings(BaseSettings):
    APP_NAME: str = "NetSecureLab"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = False

    # Database
    DB_URL: str = f"sqlite:///{BASE_DIR / 'netsecurelab.db'}"

    # Directory paths
    SCANS_DIR: Path = SCANS_DIR_DEFAULT
    REPORTS_DIR: Path = REPORTS_DIR_DEFAULT

    # Nmap settings
    NMAP_PATH: str = "nmap"
    SCAN_TIMEOUT: int = 600  # seconds
    MAX_SCAN_TIMEOUT: int = 1800  # hard ceiling (30 mins)
    OS_DETECTION_ENABLED: bool = True

    @field_validator("SCAN_TIMEOUT")
    @classmethod
    def validate_scan_timeout(cls, v: int) -> int:
        return min(max(30, v), 1800)

    # Scan profiles (backend-controlled, never arbitrary input from frontend)
    SCAN_PROFILES: Dict[str, List[str]] = {
        "quick": ["-sn"],
        "standard": ["-sV", "-T4", "--top-ports", "1000"],
        "full": ["-sV", "-sC", "-T4", "-p-"],
    }

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

# Ensure scans and reports directories exist
settings.SCANS_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

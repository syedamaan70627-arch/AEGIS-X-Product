"""
AEGIS-X API Configuration Module.

Provides environment-configurable settings for local development and production Supabase deployments.
"""

import os
from pathlib import Path
from typing import List, Set


class Settings:
    """Application settings for AEGIS-X REST API."""

    API_TITLE: str = "AEGIS-X API"
    API_DESCRIPTION: str = "Model-Agnostic AI Reliability Analysis API"
    API_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Base project directory resolved cleanly
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Environment & Backend Configuration
    AEGIS_ENV: str = os.getenv("AEGIS_ENV", "development")
    DATABASE_BACKEND: str = os.getenv("DATABASE_BACKEND", "sqlite").lower()  # "sqlite" or "supabase"
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local").lower()      # "local" or "supabase"
    AUTH_REQUIRED: bool = os.getenv("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")

    # Supabase Credentials (loaded from environment)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "aegis-private")

    # CORS Allowed Origins & Narrow Vercel Preview Regex
    _raw_cors: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://aegis-x-product.vercel.app")
    CORS_ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]
    CORS_ALLOWED_ORIGIN_REGEX: Optional[str] = os.getenv(
        "CORS_ALLOWED_ORIGIN_REGEX",
        r"^https://aegis-x-product-[a-z0-9-]+-syedamaan70627-4156s-projects\.vercel\.app$",
    )


    # Storage directory defaults (relative to project root, overridable by environment variable)
    STORAGE_DIR: Path = Path(os.getenv("AEGIS_STORAGE_DIR", BASE_DIR / "storage"))

    MODELS_DIR: Path = STORAGE_DIR / "models"
    DATASETS_DIR: Path = STORAGE_DIR / "datasets"
    RESULTS_DIR: Path = STORAGE_DIR / "results"
    ARTIFACTS_DIR: Path = STORAGE_DIR / "artifacts"
    API_DIR: Path = STORAGE_DIR / "api"
    DB_PATH: Path = API_DIR / "aegis.db"

    # Upload & Security Safeguards
    ALLOWED_MODEL_EXTENSIONS: Set[str] = {".joblib", ".pkl"}
    ALLOWED_DATASET_EXTENSIONS: Set[str] = {".csv"}
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("AEGIS_MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50 MB default

    @classmethod
    def ensure_directories(cls) -> None:
        """Safely create required storage directories if they do not exist."""
        for directory in [
            cls.STORAGE_DIR,
            cls.MODELS_DIR,
            cls.DATASETS_DIR,
            cls.RESULTS_DIR,
            cls.ARTIFACTS_DIR,
            cls.API_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()

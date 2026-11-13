from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/attendora"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/attendora"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # App
    APP_NAME: str = "ATTENDORA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Face Recognition
    FACE_RECOGNITION_TOLERANCE: float = 0.45
    FACE_RECOGNITION_MODEL: str = "hog"
    MIN_FACE_CONFIDENCE: float = 0.6

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Super Admin
    SUPER_ADMIN_EMAIL: str = "admin@attendora.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@12345"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "faces"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "logos"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "profiles"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "imports"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "exports"), exist_ok=True)

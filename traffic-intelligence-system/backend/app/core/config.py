"""Central settings. Values come from environment variables (set in .env / docker-compose.yml)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Traffic Intelligence System"
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "ChangeMe123!"

    # Web
    CORS_ORIGINS: str = "http://localhost:5173"

    # Files (paths inside the Docker container; see docker-compose volumes)
    UPLOAD_DIR: str = "/datasets/raw_videos"
    PROCESSED_DIR: str = "/datasets/processed_videos"
    MODEL_PATH: str = "/models/yolov8n.pt"
    MAX_UPLOAD_MB: int = 2000

    # AI
    YOLO_CONF: float = 0.35
    FRAME_STRIDE: int = 1            # 1 = every frame, 2 = every 2nd frame (faster on CPU)
    BUCKET_SECONDS: int = 60         # statistics are stored per bucket of video time
    DEFAULT_FPS: float = 25.0

    # Congestion thresholds, in PCU (passenger car units) visible in the frame on average.
    # Heuristics: tune them per camera view. See README "How congestion is calculated".
    DENSITY_LOW_MAX: float = 6.0
    DENSITY_MEDIUM_MAX: float = 15.0

    # Hour-of-day charts are grouped in this timezone
    TIMEZONE: str = "Asia/Kolkata"

    # Set false once you manage tables with Alembic migrations
    AUTO_CREATE_TABLES: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

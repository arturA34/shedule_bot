import logging
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str
    POSTGRES_USER: str = "db_user"
    POSTGRES_PASSWORD: str = "db_password"
    POSTGRES_DB: str = "schedule_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    @property
    def db_dsn(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


def get_settings() -> Settings:
    return Settings()


def setup_logging() -> None:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

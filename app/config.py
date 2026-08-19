from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent

class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class HostConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000

    @computed_field
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )
    environment: Environment = Environment.DEVELOPMENT
    host: HostConfig = HostConfig()
    api_prefix_v1: str = "/api/v1"



settings = Settings()
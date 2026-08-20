from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, PostgresDsn, SecretStr, computed_field
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


class DbConfig(BaseModel):
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("change-me")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"

    pool_size: int = 20
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    pool_timeout: int = 30

    echo: bool = False
    echo_pool: bool = False

    @computed_field
    def url(self) -> SecretStr:
        return SecretStr(
            str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=self.postgres_user,
                    password=self.postgres_password.get_secret_value(),
                    host=self.postgres_host,
                    port=self.postgres_port,
                    path=self.postgres_db,
                )
            )
        )


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
    db: DbConfig = DbConfig()


settings = Settings()

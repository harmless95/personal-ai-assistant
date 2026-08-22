from enum import StrEnum
from pathlib import Path
from urllib.parse import quote

from fastapi_structlog import LogSettings
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


class StagingConfig(BaseModel):
    max_users: int = 100


class AuthJWTConfig(BaseModel):
    secret_key: SecretStr = SecretStr("change-me-to-secure-key-min-32-chars!!")
    algorithm_jwt: str = "HS256"
    token_type: str = "Bearer"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


class OpenAIConfig(BaseModel):
    api_key: SecretStr = SecretStr("")
    model: str = "gpt-4.1-mini"
    max_completion_tokens: int = 1024
    enabled: bool = True
    input_price_per_1m_tokens: float = 0.40
    output_price_per_1m_tokens: float = 1.60


class RedisConfig(BaseModel):
    url: SecretStr | None = None
    host: str = "localhost"
    port: int = 6379
    user: str | None = None
    password: SecretStr | None = None
    socket_timeout: int = 10
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30

    @computed_field
    def connection_url(self) -> SecretStr:
        if self.url is not None:
            return self.url
        if self.password is None:
            return SecretStr(f"redis://{self.host}:{self.port}/0")
        auth_user = quote(self.user or "", safe="")
        password = quote(self.password.get_secret_value(), safe="")
        return SecretStr(f"redis://{auth_user}:{password}@{self.host}:{self.port}/0")


class TaskiqConfig(BaseModel):
    queue_name: str = "taskiq_queue"
    max_connection_pool_size: int = 20
    default_retry_count: int = 3
    day_summary_max_retries: int = 3
    day_summary_retry_on_error: bool = True


class DaySummaryConfig(BaseModel):
    provider: str = "openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )
    environment: Environment = Environment.DEVELOPMENT
    staging: StagingConfig = StagingConfig()
    auth_jwt: AuthJWTConfig = AuthJWTConfig()
    openai: OpenAIConfig = OpenAIConfig()
    day_summary: DaySummaryConfig = DaySummaryConfig()
    redis: RedisConfig = RedisConfig()
    taskiq: TaskiqConfig = TaskiqConfig()
    host: HostConfig = HostConfig()
    api_prefix_v1: str = "/api/v1"
    db: DbConfig = DbConfig()
    log: LogSettings = LogSettings()


settings = Settings()

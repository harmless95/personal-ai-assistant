from pathlib import Path

from pydantic import BaseModel, PostgresDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class RunAppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051


class DbConfig(BaseModel):
    postgres_user: str = "postgres"
    postgres_password: SecretStr = SecretStr("change-me")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"

    pool_size: int = 5
    max_overflow: int = 5
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


class RAGConfig(BaseModel):
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    # Must match knowledge_services.db.constants.EMBEDDING_DIMENSIONS / migration.
    embedding_dimensions: int = 768
    chunk_size: int = 800
    chunk_overlap: int = 100


class S3Config(BaseModel):

    endpoint_url: str = "http://localhost:9000"
    access_key: SecretStr = SecretStr("minioadmin")
    secret_key: SecretStr = SecretStr("minioadmin")
    bucket: str = "knowledge"
    region: str = "us-east-1"
    # Path-style addressing is required for MinIO.
    force_path_style: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )
    run: RunAppConfig = RunAppConfig()
    db: DbConfig = DbConfig()
    rag: RAGConfig = RAGConfig()
    s3: S3Config = S3Config()


settings = Settings()

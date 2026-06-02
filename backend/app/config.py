from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NRL Medical Claim Engine"
    debug: bool = True

    database_url: str = "postgresql://medclaim:medclaim@localhost:5432/medclaim"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "workshop-dev-secret-change-in-prod"
    access_token_expire_minutes: int = 480

    upload_dir: str = "uploads"
    llm_base_url: str = "http://host.docker.internal:11434"
    llm_model: str = "llama3.2"
    sap_use_mock: bool = True

    ocr_confidence_threshold: float = 0.65


settings = Settings()

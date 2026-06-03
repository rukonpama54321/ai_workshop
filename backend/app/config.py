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

    # LLM: "ollama" (self-hosted, default) or "groq" (free hosted API for demo).
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    llm_vision_model: str = "llama3.2-vision"
    # Groq (OpenAI-compatible). Set LLM_PROVIDER=groq + LLM_API_KEY to enable.
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str = ""

    sap_use_mock: bool = True

    ocr_confidence_threshold: float = 0.65

    # Email: "none" (default), "resend", or "smtp".
    email_provider: str = "none"
    resend_api_key: str = ""
    email_from: str = "onboarding@resend.dev"
    frontend_url: str = "http://127.0.0.1:5173"


settings = Settings()

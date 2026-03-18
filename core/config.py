"""
Configurações centralizadas via variáveis de ambiente.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Banco de dados
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "postgres"
    DB_PORT: int = 5432

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # IA
    GROQ_API_KEY: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 dias

    # OAuth Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    GOOGLE_API_KEY: str = "dummy_key_for_test"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "db"
    POSTGRES_HOST: str = "postgres"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

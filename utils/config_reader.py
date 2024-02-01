from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    tgbot_api_key: SecretStr
    host: SecretStr
    port: SecretStr
    login: SecretStr
    password: SecretStr
    database: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()

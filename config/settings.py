from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):


    #MY SQL Credentials
    MYSQL_HOST:str
    MYSQL_PORT:int
    MYSQL_USER:str
    MYSQL_PASSWORD:str
    MYSQL_DATABASE:str

    #Proxy
    USE_PROXY: bool = False
    PROXY_PROVIDER: Optional[str] = None
    PROXY_HOST: Optional[str] = None
    PROXY_PORT: int | None = None
    PROXY_USERNAME: Optional[str] = None
    PROXY_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file= ".env",
        env_file_encoding="utf-8",
    )

@lru_cache
def get_settings() -> Settings:

    return Settings()

settings = get_settings()
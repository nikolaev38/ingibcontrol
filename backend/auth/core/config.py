# -*- encoding: utf-8 -*-
import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent
load_dotenv()

class ConfigurationDB(BaseModel):
    #########################
    #  PostgreSQL database  #
    #########################
    async_url: str = '{}://{}:{}@{}/{}'.format(
        os.getenv('DB_ENGINE_ASYNC'),
        os.getenv('DB_USERNAME'),
        os.getenv('DB_PASS'),
        os.getenv('DB_HOST'),
        os.getenv('DB_NAME')
    )
    fastapi_echo: bool = False
    aiogram_echo: bool = False
    sync_url: str = '{}://{}:{}@{}/{}'.format(
        os.getenv('DB_ENGINE_SYNC'),
        os.getenv('DB_USERNAME'),
        os.getenv('DB_PASS'),
        os.getenv('DB_HOST'),
        os.getenv('DB_NAME')
    )


class ConfigurationCORS(BaseModel):
    #########################
    #         CORS          #
    #########################
    frontend_dev_url: str = os.getenv('FRONTEND_DEV_URL')
    frontend_prod_url: str = os.getenv('FRONTEND_PROD_URL')
    frontend_urls: list = [
        frontend_prod_url,
        frontend_dev_url,
    ]


class AuthorizationJWT(BaseModel):
    #########################
    #        TOKENS         #
    #########################
    private_key_path: Path = BASE_DIR / 'certs' / 'jwt-private.pem'
    public_key_path: Path = BASE_DIR / 'certs' / 'jwt-public.pem'
    algorithm: str = 'RS256'
    
    access_token_expire_minutes: int = 15           # Токен доступа (15 минут)
    refresh_token_expire_minutes: int = 10080       # Токен обновления (7 дней = 7 * 24 * 60 = 10080 минут)


class ConfigurationLoki(BaseModel):
    #########################
    #         Loki          #
    #########################
    url: str = os.getenv('LOKI_URL')

class Setting(BaseSettings):
    # GLOBAL
    # location_timezone: str = 'Europe/Moscow' # +3
    location_timezone: str = 'UTC'

    # FASTAPI
    api_site_v1_prefix: str = '/api_site/v1'
    
    # LOKI
    loki: ConfigurationLoki = ConfigurationLoki()
    
    db: ConfigurationDB = ConfigurationDB()
    cors: ConfigurationCORS = ConfigurationCORS()
    auth_jwt: AuthorizationJWT = AuthorizationJWT()

    email_max_len: int = 128
    password_max_len: int = 64

    referral_key_max_len: int = 128

settings = Setting()
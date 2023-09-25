from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import datetime

class JwtSettings(BaseModel):
    ALGORITHM: str = "HS512"
    ACCESS_TOKEN_EXPIRES: int = 60 * 60 * 12 # seconds

class CacheSettings(BaseModel):
    TYPE: str = "RedisCache"
    DEFAULT_TIMEOUT: int = 60 * 5 # seconds
    KEY_PREFIX: str = "ailurus_"
    REDIS_URL: str

class CelerySettings(BaseModel):
    BROKER_URL: str
    BROKER_CONNECTION_RETRY_ON_STARTUP: bool = True
    RESULT_BACKEND: str = ""
    TASK_IGNORE_RESULT: bool = True

class AdceSettings(BaseSettings):
    SECRET: str
    EVENT_NAME: str = "Ailurus"
    LOGO_URL: str
    SERVER_MODE: str = "private"
    REMOTE_DIR: str = "/opt/adce_data"
    
    FLAG_FORMAT: str = "flag{__RANDOM__}"
    FLAG_RNDLEN: int = 32

    START_TIME: str = "2037-01-01T00:00:00Z"
    FREEZE_TIME: str = "2037-01-01T00:00:00Z"
    NUMBER_ROUND: int = 5
    NUMBER_TICK: int = 6
    TICK_DURATION: int = 60 * 5 # seconds
    
    
class PlatformSettings(BaseSettings):
    SECRET_KEY: str
    SQLALCHEMY_DATABASE_URI: str
    CORS_ORIGIN: List[str] = list()

    CACHE: CacheSettings
    CELERY: CelerySettings
    ADCE: AdceSettings

    model_config = SettingsConfigDict(env_prefix='FLASK_', env_nested_delimiter='__')
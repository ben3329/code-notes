from common.singletone import SingletonMeta
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")
    user: str
    password: str
    host: str
    port: int
    database: str
    pool_size: int = 5
    max_overflow: int = 10


class DBEngine(metaclass=SingletonMeta):
    def __init__(self):
        config = DBSettings()
        self._engine = create_engine(
            "mysql+pymysql://{user}:{password}@{host}:{port}/{database}".format(
                user=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database,
            ),
            pool_pre_ping=True,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
        )
        self.__aio_engine = create_async_engine(
            "mysql+aiomysql://{user}:{password}@{host}:{port}/{database}".format(
                user=config.user,
                password=config.password,
                host=config.host,
                port=config.port,
                database=config.database,
            ),
            pool_pre_ping=True,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
        )
        self._AsyncSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.__aio_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self):
        return self._engine

    @property
    def AsyncSessionLocal(self):
        return self._AsyncSessionLocal

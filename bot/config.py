import os
from environs import Env
from dataclasses import dataclass


ENV_VAR_PREFIX = 'FPB_'


@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    ADMINS: list[int]
    REDIS_IP: str
    REDIS_PORT: int
    REDIS_DB: int


def load_config() -> Config:
    env = Env()
    env.read_env()

    config = Config(
        BOT_TOKEN=env.str(ENV_VAR_PREFIX + 'BOT_TOKEN'),
        ADMINS=env.list(ENV_VAR_PREFIX + 'ADMINS'),
        REDIS_IP=env.str(ENV_VAR_PREFIX + 'REDIS_IP'),
        REDIS_PORT=env.int(ENV_VAR_PREFIX + 'REDIS_PORT'),
        REDIS_DB=env.int(ENV_VAR_PREFIX + 'REDIS_DB')
    )

    clear_env_vars()
    return config


def clear_env_vars():
    for env_var in tuple(os.environ):
        if env_var.startswith(ENV_VAR_PREFIX):
            os.environ.pop(env_var)

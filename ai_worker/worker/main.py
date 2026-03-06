from arq.connections import RedisSettings

from worker import config


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions: list = []  # 태스크 함수들은 Phase 3에서 등록

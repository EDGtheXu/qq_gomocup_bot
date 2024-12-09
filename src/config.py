from nonebot import get_driver
from nonebot.config import BaseSettings
from pydantic import field_validator


class Config(BaseSettings):

    owner_id: int
    bot_id: int

    command_priority: int = 1
    command_block : bool = False
    project_root: str = r'D:\programingFiles\qqplugin\gomocup'

    @field_validator("command_priority")
    @classmethod
    def check_priority(cls, v: int) -> int:
        if v >= 1:
            return v
        raise ValueError("command priority must greater than 1")


global_config = get_driver().config
cfg = Config.model_validate(global_config.dict())

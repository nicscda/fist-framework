from typing import Annotated, ClassVar

from pydantic import Field

from ..utils.vocabularies import Platform, ToolType
from .utils.base import Base, duplicate_validator


class Tool(Base, title="工具"):
    """工具資料模型，用於紀錄技術或偵測、緩解等各種情境下使用的各種工具、軟體和服務。"""

    _pattern: ClassVar = r"^TL[0-9]{4}$"

    platforms: Annotated[
        list[Platform],
        Field(
            title="平台",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tool_types: Annotated[
        list[ToolType],
        Field(
            title="工具類型",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tool_version: Annotated[
        str | None,
        Field(
            title="工具版本",
            default=None,
        ),
    ]

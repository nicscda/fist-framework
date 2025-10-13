from typing import Annotated, ClassVar, override

from pydantic import Field, computed_field

from ..utils.vocabularies import CollectionLayer, Platform
from .utils.base import Base, duplicate_validator


class Detection(Base, title="偵測資料"):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._folder = "detections"


class Source(Detection, title="偵測來源"):
    """偵測來源資料模型，用於紀錄各種管道收集的各種資訊主題。"""

    _pattern: ClassVar = r"^D[0-9]{4}$"

    platforms: Annotated[
        list[Platform],
        Field(
            title="平台",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    collection_layers: Annotated[
        list[CollectionLayer],
        Field(
            title="收集層",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]


class Component(Detection, title="偵測元件"):
    """偵測元件資料模型，用於紀錄各個資料來源涵蓋的資料組件，指識別與檢測特定技術相關的資料來源的具體屬性或值。"""

    _pattern: ClassVar = r"^D[0-9]{4}\.[0-9]{3}$"

    @computed_field(return_type=str)  # type: ignore[prop-decorator]
    @property
    def parent_id(self):
        return self.id.rsplit(".", 1)[0]

    @classmethod
    @override
    def auto_id(cls, table: list, *, parent_id: str | None = None, **kwargs):
        if not parent_id:
            raise RuntimeError("Parent is required, please select or create a new one.")
        elif _ := [_ for _ in table if isinstance(_, cls) and _.parent_id == parent_id]:
            return super().auto_id(_, end=999)
        elif any(isinstance(_, Source) and _.id == parent_id for _ in table):
            return f"{parent_id}.001"
        else:
            raise RuntimeError(f"Missing parent {parent_id!r}, please create it first.")

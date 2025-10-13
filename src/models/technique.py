import re
from typing import Annotated, ClassVar, override

from pydantic import AliasChoices, Field, StringConstraints, computed_field

from ..utils.vocabularies import Permission, Platform
from .detection import Component
from .mitigation import Mitigation
from .tactic import Tactic
from .tool import Tool
from .utils.base import Base, duplicate_validator
from .utils.item_group import Group, Item


class DetectionComponent(Item, title="偵測元件"):

    _pattern: ClassVar = Component._pattern


class DetectionInformation(Group[DetectionComponent], title="偵測資訊"):

    _items_info: ClassVar = dict(title="偵測元件", alias="components")


class MitigationInformation(Item, title="緩解措施"):

    _pattern: ClassVar = Mitigation._pattern


class ToolInformation(Item, title="使用工具"):

    _pattern: ClassVar = Tool._pattern


class Technique(Base, title="技術"):
    """技術資料模型，用於紀錄對手「如何」透過執行特定行動或手段達成其戰術目標。"""

    _pattern: ClassVar = r"^T[0-9]{4}(?:\.[0-9]{3})?$"

    tactic_id: Annotated[
        str,
        StringConstraints(
            to_upper=True,
            pattern=re.compile(Tactic._pattern, re.IGNORECASE),
        ),
        Field(
            title="隸屬戰術編號",
            validation_alias=AliasChoices("tactic", "tactic_id"),
        ),
    ]
    permissions: Annotated[
        list[Permission],
        Field(
            title="權限",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    platforms: Annotated[
        list[Platform],
        Field(
            title="平台",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tools: Annotated[
        list[ToolInformation],
        Field(
            title="工具資訊",
            description="利用的工具，包含軟體服務等。",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    mitigations: Annotated[
        list[MitigationInformation],
        Field(
            title="緩解資訊",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    detection: Annotated[
        DetectionInformation,
        Field(
            title="偵測資訊",
            default_factory=DetectionInformation,
        ),
    ]

    @computed_field(return_type=str | None)  # type: ignore[prop-decorator]
    @property
    def parent_id(self):
        return self.id.rsplit(".", 1)[0] if "." in self.id else None

    @classmethod
    @override
    def auto_id(cls, table: list, *, parent_id: str | None = None, **kwargs):
        if not parent_id:
            return super().auto_id(table)
        elif _ := [_ for _ in table if isinstance(_, cls) and _.parent_id == parent_id]:
            return super().auto_id(_, end=999)
        elif any(isinstance(_, cls) and _.id == parent_id for _ in table):
            return f"{parent_id}.001"
        else:
            raise RuntimeError(f"Missing parent {parent_id!r}, please create it first.")

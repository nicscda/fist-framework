import re
from typing import Annotated, ClassVar, override

from pydantic import AliasChoices, Field

from ..utils.vocabularies import (
    IdentityClass,
    IndustrySector,
    OrganizationType,
    Reliability,
)
from .utils.base import Base, duplicate_validator


class Contributor(Base, title="貢獻者"):
    """貢獻者資料模型，用於紀錄本框架的知識庫貢獻者名單資訊。"""

    _pattern: ClassVar = r"^[A-Z0-9_]{1,100}$"

    type: Annotated[
        IdentityClass,
        Field(
            title="身分類型",
            validation_alias=AliasChoices("type", "class"),
        ),
    ]
    contact: Annotated[
        str | None,
        Field(
            title="聯絡資訊",
            default=None,
            allow_multiple_lines=True,
        ),
    ]
    firstname: Annotated[
        str | None,
        Field(
            title="名字",
            default=None,
        ),
    ]
    lastname: Annotated[
        str | None,
        Field(
            title="姓氏",
            default=None,
        ),
    ]
    organization_type: Annotated[
        OrganizationType | None,
        Field(
            title="組織類型",
            default=None,
        ),
    ]
    reliability: Annotated[
        Reliability | None,
        Field(
            title="可靠性",
            default=None,
        ),
    ]
    sectors: Annotated[
        list[IndustrySector],
        Field(
            title="產業",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]

    @classmethod
    @override
    def auto_id(cls, table: list, *, prefix: str = "", **kwargs):
        # Auto-santized prefix (case-insensitive)
        prefix = (cls._type[:2] if not prefix.isalpha() else prefix).upper()
        if _ := [
            _
            for _ in table
            if isinstance(_, cls) and re.match(rf"{prefix}[0-9]+", _.id)
        ]:
            return super().auto_id(_)
        else:
            return f"{prefix}0001"

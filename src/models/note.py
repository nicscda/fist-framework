import re
from typing import Annotated, ClassVar

from pydantic import AliasChoices, Field, StringConstraints

from ..utils.vocabularies import NoteType
from .detection import Component, Source
from .mitigation import Mitigation
from .technique import Technique
from .tool import Tool
from .utils.base import Base, duplicate_validator


class Note(Base, title="筆記"):
    """筆記資料模型，用於紀錄或保留任何框架內引用到的資訊，例如：佐證資料、媒體訊息等等。"""

    _pattern: ClassVar = r"^N[0-9]{4}$"

    note_types: Annotated[
        list[NoteType],
        Field(
            title="筆記類型",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    related_ids: Annotated[
        list[
            Annotated[
                str,
                StringConstraints(
                    to_upper=True,
                    pattern=re.compile(
                        "|".join(
                            (
                                Component._pattern,
                                Source._pattern,
                                Mitigation._pattern,
                                Technique._pattern,
                                Tool._pattern,
                            )
                        ),
                        re.IGNORECASE,
                    ),
                ),
            ]
        ],
        Field(
            title="相關資料編號",
            validation_alias=AliasChoices("related_entities", "related_ids"),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]

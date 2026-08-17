from gettext import gettext as _
from typing import Annotated, ClassVar

from pydantic import Field

from ..utils.vocabularies import Platform, ToolType
from .utils.base import Base, duplicate_validator


class Tool(Base, title=_("tool").title()):
    """Software or utility used by adversaries or defenders."""

    _pattern: ClassVar = r"^TL[0-9]{4}$"

    platforms: Annotated[
        list[Platform],
        Field(
            title=_("platform").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tool_types: Annotated[
        list[ToolType],
        Field(
            title=_("tool type").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tool_version: Annotated[
        str | None,
        Field(
            title=_("tool version").title(),
            default=None,
        ),
    ]

import re
from gettext import gettext as _
from typing import Annotated, ClassVar, override

from pydantic import AliasChoices, Field, StringConstraints, computed_field

from ..utils.vocabularies import Permission, Platform
from .detection import Component
from .mitigation import Mitigation
from .tactic import Tactic
from .tool import Tool
from .utils.base import Base, duplicate_validator
from .utils.item_group import Group, Item


class ToolInformation(Item, title=_("tool information").title()):

    _pattern: ClassVar = Tool._pattern


class MitigationInformation(Item, title=_("mitigation").title()):

    _pattern: ClassVar = Mitigation._pattern


class DetectionComponent(Item, title=_("detection component").title()):

    _pattern: ClassVar = Component._pattern


class DetectionInformation(
    Group[DetectionComponent], title=_("detection information").title()
):
    _items_field_options: ClassVar = {
        "title": _("detection component").title(),
        "alias": "components",
    }


class Technique(Base, title=_("technique").title()):
    """Adversary action for achieving tactical objectives."""

    _pattern: ClassVar = r"^T[0-9]{4}(?:\.[0-9]{3})?$"

    tactic_id: Annotated[
        str,
        StringConstraints(
            to_upper=True,
            pattern=re.compile(Tactic._pattern, re.IGNORECASE),
        ),
        Field(
            title=_("tactic id").title(),
            description=_("Tactic to which it belongs."),
            validation_alias=AliasChoices("tactic", "tactic_id"),
        ),
    ]
    permissions: Annotated[
        list[Permission],
        Field(
            title=_("permission").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    platforms: Annotated[
        list[Platform],
        Field(
            title=_("platform").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    tools: Annotated[
        list[ToolInformation],
        Field(
            title=_("tool information").title(),
            description=_("Tools used, including software services, etc."),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    mitigations: Annotated[
        list[MitigationInformation],
        Field(
            title=_("mitigation").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    detection: Annotated[
        DetectionInformation,
        Field(
            title=_("detection information").title(),
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
            return super().auto_id(
                [e for e in table if isinstance(e, cls) and not e.parent_id],
                **kwargs,
            )
        elif siblings := [
            e for e in table if isinstance(e, cls) and e.parent_id == parent_id
        ]:
            return super().auto_id(siblings, end=999, **kwargs)
        elif any(isinstance(e, cls) and e.id == parent_id for e in table):
            return f"{parent_id}.001"
        else:
            raise ValueError(
                _("Missing parent {parent!r}, please create it first.").format(
                    parent=parent_id
                )
            )

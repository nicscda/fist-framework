from gettext import gettext as _
from typing import Annotated, ClassVar, override

from pydantic import Field, computed_field

from ..utils.vocabularies import CollectionLayer, Platform
from .utils.base import Base, duplicate_validator


class Detection(Base, title=_("detection").title()):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._group = "detections"


class Source(Detection, title=_("detection source").title()):
    """Detection data source collected through various channels."""

    _pattern: ClassVar = r"^D[0-9]{4}$"

    platforms: Annotated[
        list[Platform],
        Field(
            title=_("platform").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    collection_layers: Annotated[
        list[CollectionLayer],
        Field(
            title=_("collection layer").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]


class Component(Detection, title=_("detection component").title()):
    """Data attribute or value for identifying and detecting specific techniques."""

    _pattern: ClassVar = r"^D[0-9]{4}\.[0-9]{3}$"

    @computed_field(return_type=str)  # type: ignore[prop-decorator]
    @property
    def parent_id(self):
        return self.id.rsplit(".", 1)[0]

    @classmethod
    @override
    def auto_id(cls, table: list, *, parent_id: str | None = None, **kwargs):
        if not parent_id:
            raise ValueError(
                _("Parent is required, please select or create a new one.")
            )
        elif siblings := [
            e for e in table if isinstance(e, cls) and e.parent_id == parent_id
        ]:
            return super().auto_id(siblings, end=999, **kwargs)
        elif any(isinstance(e, Source) and e.id == parent_id for e in table):
            return f"{parent_id}.001"
        else:
            raise ValueError(
                _("Missing parent {parent!r}, please create it first.").format(
                    parent=parent_id
                )
            )

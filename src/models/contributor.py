import re
from gettext import gettext as _
from typing import Annotated, ClassVar, override

from pydantic import Field, HttpUrl, computed_field

from ..utils.vocabularies import (
    IdentityClass,
    IndustrySector,
    OrganizationType,
    Reliability,
)
from .utils.base import Base, duplicate_validator


class Contributor(Base, title=_("contributor").title()):
    """Framework knowledge base contributors."""

    _pattern: ClassVar = r"^[A-Z0-9_]{1,100}$"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._group = "contributors"

    roles: Annotated[
        list[str],
        Field(
            title=_("role").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    sectors: Annotated[
        list[IndustrySector],
        Field(
            title=_("industry sector").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    contact_information: Annotated[
        str | None,
        Field(
            title=_("contact information").title(),
            default=None,
            json_schema_extra={"multiline": True},
        ),
    ]
    reliability: Annotated[
        Reliability | None,
        Field(
            title=_("reliability").title(),
            default=None,
        ),
    ]
    headshot: Annotated[
        HttpUrl | None,
        Field(
            title=_("headshot").title(),
            default=None,
        ),
    ]

    @computed_field(return_type=IdentityClass)  # type: ignore[prop-decorator]
    @property
    def identity_class(self):
        return IdentityClass[self._type.upper()]

    @classmethod
    @override
    def auto_id(cls, table: list, *, prefix: str = "", **kwargs):
        # Auto-santized prefix (case-insensitive).
        prefix = (
            prefix if prefix.isalpha() else f"{cls._group[0]}{cls._type[0]}"
        ).upper()
        pattern = re.compile(rf"{prefix}[0-9]+", re.IGNORECASE)
        if __ := [e for e in table if isinstance(e, cls) and pattern.match(e.id)]:
            return super().auto_id(__, **kwargs)
        else:
            return f"{prefix}0001"


class Individual(Contributor, title=_("individual contributor").title()):

    firstname: Annotated[
        str | None,
        Field(
            title=_("firstname").title(),
            default=None,
        ),
    ]
    lastname: Annotated[
        str | None,
        Field(
            title=_("lastname").title(),
            default=None,
        ),
    ]


class Organization(Contributor, title=_("organizational contributor").title()):

    organization_type: Annotated[
        OrganizationType | None,
        Field(
            title=_("organization type").title(),
            default=None,
        ),
    ]

from enum import StrEnum, unique
from gettext import gettext as _
from types import DynamicClassAttribute

from stix2.v21.vocab import (
    IDENTITY_CLASS_INDIVIDUAL,
    IDENTITY_CLASS_ORGANIZATION,
    INDUSTRY_SECTOR,
    TOOL_TYPE,
)


class CustomEnum(StrEnum):
    """Base enumeration class with displayname."""

    _displayname_: str

    @DynamicClassAttribute
    def displayname(self):
        """The displayname of the Enum member."""
        return self._displayname_

    def __new__(cls, *values):
        if 2 < len(values):
            raise TypeError(f"too many arguments for str(): {values!r}")
        for value in values:
            if not isinstance(value, str):
                raise TypeError(f"{value!r} is not a string")

        member = str.__new__(cls, values[0])
        member._value_ = values[0]
        member._displayname_ = str(values[1]) if 2 == len(values) else values[0]
        return member


@unique
class CollectionLayer(StrEnum):
    """Collection layers vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    CLOUD_CONTROL_PLANE = "cloud-control-plane"
    CONTAINER = "container"
    HOST = "host"
    NETWORK = "network"
    OSINT = "OSINT"


@unique
class IdentityClass(CustomEnum):
    """Identity vocabulary."""

    locals().update(
        (s.upper(), (s, _(s)))
        for s in (IDENTITY_CLASS_INDIVIDUAL, IDENTITY_CLASS_ORGANIZATION)
    )


@unique
class IndustrySector(StrEnum):
    """Industry sectors vocabulary."""

    locals().update((s.upper(), s) for s in INDUSTRY_SECTOR)


@unique
class NoteType(StrEnum):
    """Note types vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    ANALYSIS = "analysis"
    ASSESSMENT = "assessment"
    EXTERNAL = "external"
    FEEDBACK = "feedback"
    INTERNAL = "internal"


@unique
class OrganizationType(StrEnum):
    """Organization types vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    CONSTITUENT = "constituent"
    CSIRT = "csirt"
    OTHER = "other"
    PARTNER = "partner"
    VENDOR = "vendor"


@unique
class Platform(StrEnum):
    """Platforms vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    ANDROID = "android"
    AZURE_AD = "Azure AD"
    CONTAINERS = "Containers"
    CONTROL_SERVER = "Control Server"
    DATA_HISTORIAN = "Data Historian"
    ENGINEERING_WORKSTATION = "Engineering Workstation"
    FIELD_CONTROLLER = "Field Controller/RTU/PLC/IED"
    GOOGLE_WORKSPACE = "Google Workspace"
    HUMAN_MACHINE_INTERFACE = "Human-Machine Interface"
    IAAS = "IaaS"
    IO_SERVER = "Input/Output Server"  # I/O server
    IOS = "iOS"
    LINUX = "linux"
    MACOS = "macos"
    OFFICE_365 = "Office 365"
    PRE = "PRE"
    SAAS = "SaaS"
    SIS_PROTECTION_RELAY = "Safety Instrumented System/Protection Relay"
    WINDOWS = "windows"


@unique
class Permission(StrEnum):
    """Permissions vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    ADMINISTRATOR = "Administrator"
    ROOT = "root"  # aka: superuser
    USER = "User"


@unique
class Reliability(CustomEnum):
    """Reliability vocabulary.

    .. seealso::
        [Taxonomy - OpenCTI Documentation](https://docs.opencti.io/latest/reference/taxonomy)
    """

    COMPLETELY_RELIABLE = "A", _("completely reliable")
    USUALLY_RELIABLE = "B", _("usually reliable")
    FAIRLY_RELIABLE = "C", _("fairly reliable")
    NOT_USUALLY_RELIABLE = "D", _("not usually reliable")
    UNRELIABLE = "E", _("unreliable")
    UNJUDGED = "F", _("unjudge")  # Reliability cannot be judged


@unique
class ToolType(StrEnum):
    """Tool types vocabulary."""

    locals().update((s.upper(), s) for s in TOOL_TYPE)

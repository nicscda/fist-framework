import re
from gettext import gettext as _
from typing import Annotated, ClassVar

from pydantic import AliasChoices, Field, StringConstraints

from .phase import Phase
from .utils.base import Base


class Tactic(Base, title=_("tactic").title()):
    """Purpose or objective behind techniques."""

    _pattern: ClassVar = r"^TA[0-9]{4}$"

    phase_id: Annotated[
        str,
        StringConstraints(
            to_upper=True,
            pattern=re.compile(Phase._pattern, re.IGNORECASE),
        ),
        Field(
            title=_("phase id").title(),
            description=_("Phase to which it belongs."),
            validation_alias=AliasChoices("phase", "phase_id"),
        ),
    ]

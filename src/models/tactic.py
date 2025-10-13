import re
from typing import Annotated, ClassVar

from pydantic import AliasChoices, Field, StringConstraints

from .phase import Phase
from .utils.base import Base


class Tactic(Base, title="戰術"):
    """戰術資料模型，用於紀錄本框架技術與子技術的「原因」或目的。"""

    _pattern: ClassVar = r"^TA[0-9]{4}$"

    phase_id: Annotated[
        str,
        StringConstraints(
            to_upper=True,
            pattern=re.compile(Phase._pattern, re.IGNORECASE),
        ),
        Field(
            title="隸屬階段編號",
            validation_alias=AliasChoices("phase", "phase_id"),
        ),
    ]

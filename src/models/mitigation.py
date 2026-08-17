from gettext import gettext as _
from typing import ClassVar

from .utils.base import Base


class Mitigation(Base, title=_("mitigation").title()):
    """Course of action to prevent or mitigate technique threats."""

    _pattern: ClassVar = r"^M[0-9]{4}$"

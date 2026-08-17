from gettext import gettext as _
from typing import ClassVar

from .utils.base import Base


class Phase(Base, title=_("phase").title()):
    """Top-level grouping representing key activity milestones."""

    _pattern: ClassVar = r"^P[0-9]{4}$"

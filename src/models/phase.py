from typing import ClassVar

from .utils.base import Base


class Phase(Base, title="階段"):
    """階段資料模型，用於紀錄戰術及其相關技術的最上層分群，對應「活動」事件中的重要里程。"""

    _pattern: ClassVar = r"^P[0-9]{4}$"

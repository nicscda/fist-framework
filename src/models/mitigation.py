from typing import ClassVar

from .utils.base import Base


class Mitigation(Base, title="緩解措施"):
    """緩解措施資料模型，用於紀錄可用來「防範」特定技術危害的安全概念與科技應用。"""

    _pattern: ClassVar = r"^M[0-9]{4}$"

from typing import Iterable, OrderedDict

from pydantic import AfterValidator
from pydantic_core import PydanticCustomError


def _duplicate(_):
    if isinstance(_, Iterable) and len(OrderedDict.fromkeys(_)) != len(_):
        raise PydanticCustomError("duplicate_entry", "Duplicate entry not allowed")
    return _


duplicate_validator = AfterValidator(_duplicate)

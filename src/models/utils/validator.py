from typing import OrderedDict

from pydantic import AfterValidator
from pydantic_core import PydanticCustomError


def _raise(e: Exception):
    raise e


entry_duplicate_error = PydanticCustomError(
    "entry_duplicate",
    "Duplicate entry not allowed",
)
duplicate_validator = AfterValidator(
    lambda v: (
        _raise(entry_duplicate_error)
        if isinstance(v, list) and len(OrderedDict.fromkeys(v)) != len(v)
        else v
    )
)

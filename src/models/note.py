import re
from gettext import gettext as _
from typing import Annotated, ClassVar

from pydantic import AliasChoices, Field, StringConstraints

from ..utils.vocabularies import NoteType
from .contributor import Contributor
from .detection import Component, Source
from .mitigation import Mitigation
from .phase import Phase
from .tactic import Tactic
from .technique import Technique
from .tool import Tool
from .utils.base import Base, duplicate_validator


class Note(Base, title=_("note").title()):
    """Supplementary information such as evidence and media sources."""

    _pattern: ClassVar = r"^N[0-9]{4}$"

    note_types: Annotated[
        list[NoteType],
        Field(
            title=_("note type").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    related_ids: Annotated[
        list[
            Annotated[
                str,
                StringConstraints(
                    to_upper=True,
                    pattern=re.compile(
                        "|".join(
                            (
                                Contributor._pattern,
                                Component._pattern,
                                Source._pattern,
                                Mitigation._pattern,
                                Phase._pattern,
                                Tactic._pattern,
                                Technique._pattern,
                                Tool._pattern,
                            )
                        ),
                        re.IGNORECASE,
                    ),
                ),
            ]
        ],
        Field(
            title=_("related data id").title(),
            default_factory=list,
            max_length=100,
            validation_alias=AliasChoices("related_entities", "related_ids"),
        ),
        duplicate_validator,
    ]

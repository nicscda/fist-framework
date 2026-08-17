import json
from dataclasses import KW_ONLY, InitVar, dataclass, field, fields
from datetime import datetime
from enum import Enum
from functools import cache
from gettext import gettext as _
from operator import attrgetter
from pathlib import Path
from typing import Callable, Iterable, Literal, cast, get_origin, overload

import yaml
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

from ..utils.functions import (
    get_display_path,
    get_git_metadata,
    load_files,
    next_non_none_type,
)
from .contributor import Individual, Organization
from .detection import Component, Source
from .mitigation import Mitigation
from .note import Note
from .phase import Phase
from .tactic import Tactic
from .technique import Technique
from .tool import Tool
from .utils.base import Base

LEGAL_FILE_EXTENSIONS = (".json", ".jsonl", ".yaml", ".yml")


@dataclass(frozen=True)
class Manifest:
    """Load, validate, and organize framework data."""

    paths: InitVar[list[Path]]
    recursive: InitVar[bool] = False
    on_error: InitVar[Callable[[Path, Exception], None] | None] = None
    on_count: InitVar[Callable[[int, str | None], None] | None] = None
    _: KW_ONLY
    context: dict = field(default_factory=dict, repr=False)
    created: datetime | None = field(default=None, init=False)
    modified: datetime | None = field(default=None, init=False)
    """Additional context to pass to the validator."""
    individual_contributors: list[Individual] = field(
        default_factory=list,
        init=False,
    )
    organizational_contributors: list[Organization] = field(
        default_factory=list,
        init=False,
    )
    detection_components: list[Component] = field(
        default_factory=list,
        init=False,
    )
    detection_sources: list[Source] = field(
        default_factory=list,
        init=False,
    )
    mitigations: list[Mitigation] = field(
        default_factory=list,
        init=False,
    )
    notes: list[Note] = field(
        default_factory=list,
        init=False,
    )
    phases: list[Phase] = field(
        default_factory=list,
        init=False,
    )
    tactics: list[Tactic] = field(
        default_factory=list,
        init=False,
    )
    techniques: list[Technique] = field(
        default_factory=list,
        init=False,
    )
    tools: list[Tool] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(
        self,
        paths: list[Path],
        recursive: bool,
        on_error: Callable[[Path, Exception], None] | None,
        on_count: Callable[[int, str | None], None] | None,
    ):
        filepaths = load_files(paths, *LEGAL_FILE_EXTENSIONS, recursive=recursive)
        metadata = get_git_metadata(paths)
        object.__setattr__(
            self,
            "created",
            min(
                (ts["created"] for ts in metadata.values() if ts["created"]),
                default=None,
            ),
        )
        object.__setattr__(
            self,
            "modified",
            max(
                (ts["modified"] for ts in metadata.values() if ts["modified"]),
                default=None,
            ),
        )

        for filepath in filepaths:
            try:
                meta = metadata.get(get_display_path(filepath), {})
                match filepath.suffix.lower():
                    case ".json":
                        with open(filepath, encoding="utf-8") as f:
                            self.append(json.load(f) | meta)
                    case ".jsonl":
                        with open(filepath, encoding="utf-8") as f:
                            self.extend(
                                json.loads(line) | meta for line in f if line.strip()
                            )
                    case ".yaml" | ".yml":
                        with open(filepath, encoding="utf-8") as f:
                            self.append(yaml.safe_load(f) | meta)
            except Exception as e:
                callable(on_error) and on_error(filepath, e)
        else:
            total = 0
            for k in self.mapping().keys():
                cast(list, (table := getattr(self, k))).sort(key=attrgetter("id"))
                total += (table_count := len(table))
                callable(on_count) and on_count(table_count, k)
            else:
                callable(on_count) and on_count(total, None)

    @property
    def contributors(self):
        return self.individual_contributors + self.organizational_contributors

    @property
    def detections(self):
        return self.detection_components + self.detection_sources

    @property
    def description(self):
        return _(
            "This framework covers the complete fraud lifecycle, "
            "classifying attack tactics and techniques at each stage to support threat identification, "
            "risk assessment, and incident response."
        )

    @classmethod
    @overload
    def mapping(cls, /, *, _type: None = None) -> dict[str, type[Base]]:
        """Return the mapping of field names to model classes.

        Each key is a field name, and each value is the corresponding model class.
        Metadata fields are excluded.
        """
        pass

    @classmethod
    @overload
    def mapping(cls, /, *, _type: str) -> tuple[str, type[Base]] | None:
        """Return the mapping for a specific type.

        Looks up the field and model class for the given type name.

        .. seealso::
            :py:meth:`Base._type` and :py:meth:`Base.model_fields.get("type")`

        :param _type: Type name (e.g., "contributor" or "organization").
        :returns: A (field_name, model_class) pair, or `None` if not found.
        """
        pass

    @classmethod
    @cache
    def mapping(cls, /, *, _type: str | None = None):
        if _type is None:
            return {
                field.name: tp
                for field in fields(cls)
                if get_origin(field.type) is list
                and isinstance(tp := next_non_none_type(field.type), type)
                and issubclass(tp, Base)
                and tp is not Base
            }
        else:
            for k, v in cls.mapping().items():
                if _type == v._type:  # type: ignore[attr-defined]
                    return k, v
                elif (
                    (field := v.model_fields.get("type"))
                    and isinstance(field.annotation, type)
                    and issubclass(field.annotation, Enum)
                    and _type in field.annotation
                ):
                    return k, v
            else:
                return None

    @classmethod
    @cache
    def get_table_display_name(cls, tablename: str):
        if tp := (
            cls.mapping().get(tablename)
            or (cls.mapping(_type=tablename) or (None, None))[1]
        ):
            return cast(str, tp.model_json_schema()["title"])
        else:
            return ""

    @classmethod
    def _on_error(cls, error_type: str, data=None):
        raise ValidationError.from_exception_data(
            _("source data").title(),
            [
                InitErrorDetails(
                    type=PydanticCustomError(
                        error_type,
                        "Input should be "
                        + " or ".join(
                            (sep := ", ")
                            .join(
                                (
                                    sep.join(f"{e.value!r}" for e in field.annotation)  # type: ignore[attr-defined]
                                    if (field := v.model_fields.get("type"))
                                    and isinstance(field.annotation, type)
                                    and issubclass(field.annotation, Enum)
                                    else f"{v._type!r}"
                                )
                                for v in cls.mapping().values()
                            )
                            .rsplit(sep, 1)
                        ),
                    ),
                    loc=("type",),
                    input=data,
                )
            ],
        )

    def get_contributor(self, id: str):
        for contributor in self.contributors:
            if id == contributor.id:
                return contributor
        else:
            return None

    def get_detection_component(self, id: str):
        for component in self.detection_components:
            if id == component.id:
                return component
        else:
            return None

    def get_detection_source(self, id: str):
        for source in self.detection_sources:
            if id == source.id:
                return source
        else:
            return None

    def get_mitigation(self, id: str):
        for mitigation in self.mitigations:
            if id == mitigation.id:
                return mitigation
        else:
            return None

    def get_note(self, id: str):
        for note in self.notes:
            if id == note.id:
                return note
        else:
            return None

    def get_phase(self, id: str):
        for phase in self.phases:
            if id == phase.id:
                return phase
        else:
            return None

    def get_tactic(self, id: str):
        for tactic in self.tactics:
            if id == tactic.id:
                return tactic
        else:
            return None

    def get_tactics(self, phase_id: str):
        return [data for data in self.tactics if data.phase_id == phase_id]

    def get_technique(self, id: str):
        for technique in self.techniques:
            if id == technique.id:
                return technique
        else:
            return None

    @overload
    def get_techniques(
        self, *, component_id: str, include_meta: Literal[False] = False
    ) -> list[Technique]:
        """Obtain all detected techniques from the component."""
        pass

    @overload
    def get_techniques(
        self, *, component_id: str, include_meta: Literal[True]
    ) -> list[tuple[Technique, str | None]]:
        """Obtain all detected techniques from the component.

        Includes detection details for each technique.
        """
        pass

    @overload
    def get_techniques(
        self, *, mitigation_id: str, include_meta: Literal[False] = False
    ) -> list[Technique]:
        """Obtain all mitigated techniques in the mitigation."""
        pass

    @overload
    def get_techniques(
        self, *, mitigation_id: str, include_meta: Literal[True]
    ) -> list[tuple[Technique, str | None]]:
        """Obtain all mitigated techniques in the mitigation.

        Includes mitigation use cases for each technique.
        """
        pass

    @overload
    def get_techniques(self, *, parent_id: str) -> list[Technique]:
        """Obtain all sub-techniques belonging to the parent technique."""
        pass

    @overload
    def get_techniques(self, *, tactic_id: str) -> list[Technique]:
        """Obtain all techniques belonging to the tactic."""
        pass

    @overload
    def get_techniques(
        self, *, tool_id: str, include_meta: Literal[False] = False
    ) -> list[Technique]:
        """Obtain all techniques using the tool."""
        pass

    @overload
    def get_techniques(
        self, *, tool_id: str, include_meta: Literal[True]
    ) -> list[tuple[Technique, str | None]]:
        """Obtain all techniques using the tool.

        Includes tool use cases for each technique.
        """
        pass

    def get_techniques(self, *, include_meta=False, **kwargs):
        match (k := next(iter(kwargs), None)):
            case "component_id":
                return [
                    (technique, item.description) if include_meta else technique
                    for technique in self.techniques
                    for item in technique.detection.items
                    if kwargs[k] == item.id
                ]
            case "mitigation_id":
                return [
                    (technique, mitigation.description) if include_meta else technique
                    for technique in self.techniques
                    for mitigation in technique.mitigations
                    if kwargs[k] == mitigation.id
                ]
            case "parent_id":
                return [
                    technique
                    for technique in self.techniques
                    if kwargs[k] == technique.parent_id
                ]
            case "tactic_id":
                return [
                    technique
                    for technique in self.techniques
                    if kwargs[k] == technique.tactic_id
                ]
            case "tool_id":
                return [
                    (technique, tool.description) if include_meta else technique
                    for technique in self.techniques
                    for tool in technique.tools
                    if kwargs[k] == tool.id
                ]
            case _:
                raise TypeError(_("Missing any expected keyword argument."))

    def get_tool(self, id: str):
        for tool in self.tools:
            if id == tool.id:
                return tool
        else:
            return None

    def append(self, data: dict):
        """Identify the correct model based on the `type` field in `data`."""
        if "type" not in data:
            self._on_error("type_missing", data)
        elif pair := self.mapping(_type=str(_type := data.get("type")).lower()):
            cast(list, table := getattr(self, pair[0])).append(
                pair[1].model_validate(data, context=self.context | {"table": table})
            )
        else:
            self._on_error("type_unsupported", _type)

    @overload
    def extend(self, source: "Manifest"): ...
    @overload
    def extend(self, source: Iterable[dict]): ...

    def extend(self, source: "Manifest" | Iterable[dict]):
        if isinstance(source, Manifest):
            for k in self.mapping().keys():
                if table := cast(list, getattr(source, k)):
                    cast(list, getattr(self, k)).extend(table)
        else:
            for data in source:
                self.append(data)

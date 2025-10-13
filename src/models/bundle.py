import json
from dataclasses import KW_ONLY, InitVar, dataclass, field, fields
from enum import Enum
from functools import cache, cached_property
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable, TypeVar, cast, get_origin, overload

import yaml
from pydantic_core import PydanticCustomError, ValidationError

from ..utils.common import load_files, next_not_none_type
from .contributor import Contributor
from .detection import Component, Source
from .mitigation import Mitigation
from .note import Note
from .phase import Phase
from .tactic import Tactic
from .technique import Technique
from .tool import Tool
from .utils.base import Base, Config

T = TypeVar("T", bound=Base, covariant=True)


@dataclass(frozen=True)
class Bundle:

    kwargs: InitVar[dict]
    _: KW_ONLY
    _config: Config = field(init=False)
    contributors: list[Contributor] = field(default_factory=list, init=False)
    detection_sources: list[Source] = field(default_factory=list, init=False)
    detection_components: list[Component] = field(default_factory=list, init=False)
    mitigations: list[Mitigation] = field(default_factory=list, init=False)
    notes: list[Note] = field(default_factory=list, init=False)
    phases: list[Phase] = field(default_factory=list, init=False)
    tactics: list[Tactic] = field(default_factory=list, init=False)
    techniques: list[Technique] = field(default_factory=list, init=False)
    tools: list[Tool] = field(default_factory=list, init=False)

    def __post_init__(self, kwargs):
        object.__setattr__(self, "_config", Config(**kwargs))

    @property
    def name(self):
        return f"{self.source} Framework"

    @property
    def description(self):
        return "本框架涵蓋詐騙活動的完整生命週期，用以理解並分類各階段的攻擊與操作手法，支援威脅識別、風險評估與應變分析。"

    @property
    def filepath(self):
        return self._config.output_path

    @property
    def filename(self):
        return self._config.output

    @property
    def is_root(self):
        return not self._config.subfolder

    @property
    def source(self):
        """An ID, code or alias used to identify the source of the generated framework data."""
        return self._config.source

    @cached_property
    def subfolder_mapping(self):
        return {
            f"{k}_folder": self._config.safe_subfolder(v._folder)
            for k, v in self.mapping().items()
        }

    @classmethod
    @overload
    def mapping(cls, /) -> dict[str, type[Base]]:
        pass

    @classmethod
    @overload
    def mapping(cls, /, *, _type: str | None) -> tuple[str, type[Base]] | None:
        pass

    @classmethod
    @cache
    def mapping(cls, /, *, _type: str | None = None):
        """Mapping of field names in the bundle to their corresponding data types.

        Only useful model are collected, excluding metadata and other variables.
        """
        if _type is None:
            return {
                _.name: __
                for _ in fields(cls)
                if get_origin(_.type) is list
                and isinstance(__ := next_not_none_type(_.type), type)
                and issubclass(__, Base)
                and __ is not Base
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

    def append(self, data: dict):
        """Identify the correct model based on the `type` field in `data`."""
        if "type" not in data:
            self._on_error("missing", data)
        elif _ := self.mapping(_type=str(__ := data.get("type")).lower()):
            cast(list, table := self.__dict__[_[0]]).append(
                _[1].model_validate(
                    data, context=dict(config=self._config, table=table)
                )
            )
        else:
            self._on_error("unsupported_type", __)

    def import_data_files(
        self,
        paths: list[Path],
        recursive: bool,
        error_callback: Callable[[Path, Exception], Any] = lambda *_: ...,
        count_callback: Callable[[int, str | None], Any] = lambda *_: ...,
    ):
        if filepaths := load_files(paths, (".json", ".yaml", ".yml"), recursive):
            for filepath in filepaths:
                try:
                    match filepath.suffix.lower():
                        case ".json":
                            with open(filepath, encoding="utf-8") as file:
                                self.append(json.load(file))
                        case ".yaml" | ".yml":
                            with open(filepath, encoding="utf-8") as file:
                                self.append(yaml.safe_load(file))
                except Exception as e:
                    error_callback(filepath, e)
            else:
                total = 0
                for k in self.mapping().keys():
                    object.__setattr__(
                        self, k, sorted(table := self.__dict__[k], key=attrgetter("id"))
                    )
                    count_callback(_count := len(table), k)
                    total += _count
                else:
                    count_callback(total, None)
        else:
            count_callback(0, None)

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
        return list(filter(lambda _: _.phase_id == phase_id, self.tactics))

    def get_technique(self, id: str):
        for technique in self.techniques:
            if id == technique.id:
                return technique
        else:
            return None

    @overload
    def get_techniques(self, component_id: str) -> list[tuple[Technique, str | None]]:
        """Obtain all detected techniques from the component.

        Includes detection details for each technique.
        """
        pass

    @overload
    def get_techniques(self, mitigation_id: str) -> list[tuple[Technique, str | None]]:
        """Obtain all mitigated techniques in the mitigation.

        Includes mitigation use cases for each technique.
        """
        pass

    @overload
    def get_techniques(self, parent_id: str) -> list[Technique]:
        """Obtain all sub-techniques belonging to the parent technique."""
        pass

    @overload
    def get_techniques(self, tactic_id: str) -> list[Technique]:
        """Obtain all techniques belonging to the tactic."""
        pass

    @overload
    def get_techniques(self, tool_id: str) -> list[tuple[Technique, str | None]]:
        """Obtain all techniques using the tool.

        Includes tool use cases for each technique.
        """
        pass

    def get_techniques(self, /, **kwargs):
        result = []
        match (_ := next(iter(kwargs), None)):
            case "component_id":
                for technique in self.techniques:
                    for item in technique.detection.items:
                        if kwargs[_] == item.id:
                            result.append((technique, item.description))
                            break
            case "mitigation_id":
                for technique in self.techniques:
                    for mitigation in technique.mitigations:
                        if kwargs[_] == mitigation.id:
                            result.append((technique, mitigation.description))
                            break
            case "parent_id":
                for technique in self.techniques:
                    if kwargs[_] == technique.parent_id:
                        result.append(technique)
            case "tactic_id":
                for technique in self.techniques:
                    if kwargs[_] == technique.tactic_id:
                        result.append(technique)
            case "tool_id":
                for technique in self.techniques:
                    for tool in technique.tools:
                        if kwargs[_] == tool.id:
                            result.append((technique, tool.description))
                            break
            case _:
                raise TypeError("Missing any expected keyword argument.")

        return result

    def get_tool(self, id: str):
        for tool in self.tools:
            if id == tool.id:
                return tool
        else:
            return None

    def subpath(self, target: str | None = None, subpaths: tuple[str] = ("index.md",)):
        """Relative path to a sub-archive of specified type based on `target-directory`.

        :param target: Target type name or collection field name (e.g., `tactic` or `tactics`)
        :param *subpaths: Subpath segments, default to index page for a specific subfolder
        """
        if target is None:
            return self._config.subfolder_path.joinpath(*subpaths)
        elif (
            (_ := self.mapping().get(target))
            or (_ := self.mapping(_type=target))
            and (_ := _[1])
        ):
            return self._config.subfolder_path.joinpath(_._folder, *subpaths)  # type: ignore[attr-defined]
        else:
            return self._config.subfolder_path.joinpath(*subpaths)

    def _on_error(self, error_type: str, data=None):
        raise ValidationError.from_exception_data(
            "來源資料",
            [
                {
                    "type": PydanticCustomError(
                        error_type,
                        "Input should be "
                        + " or ".join(
                            (sep := ", ")
                            .join(
                                (
                                    sep.join(f"{e.value!r}" for e in field.annotation)  # type: ignore[attr-defined]
                                    if (field := _.model_fields.get("type"))
                                    and isinstance(field.annotation, type)
                                    and issubclass(field.annotation, Enum)
                                    else f"{_._type!r}"
                                )
                                for _ in self.mapping().values()
                            )
                            .rsplit(sep, 1)
                        ),
                    ),
                    "loc": ("type",),
                    "input": data,
                }
            ],
        )

import re
from datetime import datetime
from functools import cached_property
from gettext import gettext as _
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import (
    Field,
    FieldSerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

from ...utils.config import get_settings
from ...utils.functions import dump_yaml, get_unique_path
from .external_reference import ExternalReference
from .item_group import Item
from .validator import duplicate_validator


class Base(Item, title=_("basic Information").title()):
    """Base model for common data fields and methods."""

    _group: ClassVar[str]
    """Data group folder name. Defaults to the plural form of the category."""
    _type: ClassVar[str]
    """Category type. Defaults to the model class name."""

    revoked: Annotated[
        bool,
        Field(
            title=_("revoked").title(),
            default=False,
        ),
    ]
    name: Annotated[
        str,
        Field(
            title=_("name").title(),
            min_length=1,
            max_length=100,
        ),
    ]
    external_references: Annotated[
        list[ExternalReference],
        Field(
            title=_("external reference").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    contributors: Annotated[
        list[str],
        Field(
            title=_("contributor").title(),
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    created: Annotated[
        datetime | None,
        Field(
            default=None,
            description=_("Derived from git history; read-only for editors."),
            json_schema_extra={"readOnly": True},
        ),
    ]
    modified: Annotated[
        datetime | None,
        Field(
            default=None,
            description=_("Derived from git history; read-only for editors."),
            json_schema_extra={"readOnly": True},
        ),
    ]

    @cached_property
    def order(self):
        return int(re.sub(r"[^0-9]", "", self.id) or 0)

    @cached_property
    def url(self):
        return get_settings().get_url_path(self._group, self.id, full=True)

    @cached_property
    def external_contributors(self):
        """Get contributors excluding the default author."""
        author = get_settings().author
        author_info = (author.alias, author.name, author.email)
        return [
            contributor
            for contributor in self.contributors
            if contributor not in author_info
        ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._type = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cls.__name__).lower()
        cls._group = cls._type + "s"

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """Implement changing the order of inherited fields.

        Move some specific fields to the top and some to the bottom.

        If need more type-checkers or model-helpers, continue implementing them in this section.

        .. note::
            Computed fields cannot be sorted by the model itself as they are auto-added after all.
            If extending this model, ensure that any field reordering logic is compatible.

        .. seealso::
            :py:meth:`pydantic.BaseModel.__pydantic_init_subclass__` - https://docs.pydantic.dev/latest/api/base_model

        :param kwargs: Any keyword arguments passed to the class definition that aren't used internally by pydantic.
        """
        super().__pydantic_init_subclass__(**kwargs)
        top, middle, bottom = {}, {}, {}
        for k, v in cls.model_fields.items():
            if k in ("revoked", "id", "name") or k.endswith("_id"):
                top[k] = v
            elif k in ("external_references", "contributors"):
                bottom[k] = v
            else:
                middle[k] = v
        else:
            cls.model_fields.clear()
            cls.model_fields.update(**top, **middle, **bottom)
            cls.model_rebuild(force=True)

    @field_validator("id", "name")
    @classmethod
    def check_unique_keys(cls, value, info: ValidationInfo):
        """Verify uniqueness constraints.

        - ID must be unique across all entries (including revoked)
        - Name must be unique among active (non-revoked) entries only
        """
        if (
            not (info.data.get("revoked") and "name" == info.field_name)
            and isinstance(info.context, dict)
            and isinstance(table := info.context.get("table"), list)
            and any(
                _.__dict__[info.field_name] == value
                and not ("name" == info.field_name and _.__dict__["revoked"])
                for _ in table
            )
        ):
            raise PydanticCustomError("duplicate_entry", "Duplicate entry not allowed")

        return value

    @model_validator(mode="after")
    def resolve_url(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("skip_model_validation")
        ):
            _settings = get_settings()
            for idx, external_reference in enumerate(self.external_references):
                if self.url.split("//", 1)[-1] in str(external_reference.url or "") or (
                    _settings.project_name == external_reference.source_name
                    and self.id == external_reference.external_id
                ):
                    raise ValidationError.from_exception_data(
                        getattr(info.config, "title", type(self).__name__),
                        [
                            InitErrorDetails(
                                type=PydanticCustomError(
                                    "self_referral",
                                    "Self-referral not allowed",
                                ),
                                loc=("external_references", idx),
                                input=self.external_references,
                            )
                        ],
                    )
            else:
                if isinstance(info.context, dict) and not info.context.get(
                    "exclude_self"
                ):
                    self.external_references.insert(
                        0,
                        ExternalReference(
                            source_name=_settings.project_name,
                            description=None,
                            url=self.url,
                            external_id=self.id,
                        ),
                    )

        return self

    @field_serializer("external_references", mode="wrap", when_used="json")
    def serialize_external_references(
        self,
        external_references: list[ExternalReference],
        handler: SerializerFunctionWrapHandler,
        info: FieldSerializationInfo,
    ):
        _settings = get_settings()
        return handler(
            (
                [
                    external_reference
                    for external_reference in external_references
                    if not (
                        self.url == external_reference.url
                        or (
                            _settings.project_name == external_reference.source_name
                            and self.id == external_reference.external_id
                        )
                    )
                ]
                if isinstance(info.context, dict) and info.context.get("exclude_self")
                else external_references
            ),
            info,  # type: ignore[arg-type]
        )

    @classmethod
    def auto_id(cls, table: list, *, start=1, end=9999, **kwargs):
        if _ids := sorted({e.id for e in table if isinstance(e, cls)}):
            return re.sub(
                r"^[0-9]+$|(?<=[^0-9])[0-9]+$",
                lambda s: str(min(1 + int(s[0]), end)).zfill(len(s[0])),
                _ids[-1],
            )
        elif re.search(r"\[0-9\]\{(?:[0-9]+,)?(?P<num>[0-9]+)\}", cls._pattern):
            return re.sub(
                r"(?P<dot>\\\.)|\[0-9\]\{(?:[0-9]+,)?(?P<num>[0-9]+)\}|[^A-Z]+",
                lambda s: (
                    str(start).zfill(int(num))
                    if (num := s.group("num"))
                    else "." if s.group("dot") else ""
                ),
                cls._pattern,
            )
        else:
            return cls._type[:2].upper() + str(start).zfill(len(str(end)))

    def model_dump_yaml(self, directory: Path | None = None, overwrite=False):
        """Dump the model as a YAML string, or write to file if directory is given.

        .. note::
            File naming pattern:

            - Default: `{self.id}.yaml` (e.g., `TA01.yaml`)
            - Keep both files: `{self.id} ({attempt}).yaml` (e.g., `TA01 (1).yaml`)

        :param directory: Output directory to store file.
        :param overwrite: Replace existing file, or auto-rename to avoid conflict (default: keep both files).
        :returns: YAML string if no directory is provided, otherwise the file path if stored successfully.
        """
        s = (
            "---\n"
            + "\n".join(
                dump_yaml(
                    {"type": self._type}
                    | self.model_dump(
                        mode="json",
                        by_alias=True,
                        exclude={
                            *self.__class__.model_computed_fields.keys(),
                            "revoked",
                        },
                        exclude_none=False,
                        exclude_unset=True,
                        context={"as_relative_url": True, "exclude_self": True},
                    ),
                    section_break_keys=["external_references"],
                    plain_scalar_keys=["url"],
                    block_scalar_keys=["contact_information", "description"],
                )
            )
            + ("\nrevoked: true\n" if getattr(self, "revoked", False) else "\n")
        )
        if directory is None:
            return s
        else:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
            with open(  # type: ignore[call-overload]
                *(
                    (directory / f"{self.id}.yaml", "w")
                    if overwrite
                    else (get_unique_path(directory / f"{self.id}.yaml"), "x")
                ),
                encoding="utf-8",
            ) as f:
                f.write(s)
                return Path(f.name)

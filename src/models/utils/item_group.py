import re
from gettext import gettext as _
from typing import Annotated, ClassVar, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.fields import FieldInfo

from .validator import duplicate_validator


class Item(BaseModel):
    """Data Item for structured data generation."""

    _pattern: ClassVar[str] = ""
    """ID format, keep empty if no restrictions."""

    model_config = ConfigDict(
        title=_("data item").title(),
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
        coerce_numbers_to_str=True,
    )

    id: Annotated[
        str,
        Field(
            title=_("id").title(),
            min_length=1,
            max_length=100,
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            title=_("description").title(),
            default=None,
            json_schema_extra={"multiline": True},
        ),
    ]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """Initialize ID format with a custom pattern.

        User input is case-insensitive; enforce case-insensitive regex and convert to uppercase.

        If need more type-checkers or model-helpers, continue implementing them in this section.

        .. note::
            Computed fields cannot be sorted by the model itself as they are auto-added after all.
            If extending this model, ensure that any field reordering logic is compatible.

        .. seealso::
            :py:meth:`pydantic.BaseModel.__pydantic_init_subclass__` - https://docs.pydantic.dev/latest/api/base_model

        :param kwargs: Any keyword arguments passed to the class definition that aren't used internally by pydantic.
        """
        super().__pydantic_init_subclass__(**kwargs)
        cls.model_fields.update(
            id=FieldInfo.from_annotation(
                Annotated[
                    str,
                    cls.model_fields.get("id"),
                    StringConstraints(
                        to_upper=True,
                        pattern=(
                            re.compile(cls._pattern, re.IGNORECASE)
                            if cls._pattern
                            else None
                        ),
                    ),
                ]
            )
        )
        cls.model_rebuild(force=True)

    def __hash__(self):
        return self.id.__hash__()


T = TypeVar("T", bound=Item, covariant=True)


class Group(BaseModel, Generic[T]):
    """Data collection for structured data collections"""

    _items_field_options: ClassVar[dict] = {}
    """Additional information about `items` field (e.g., alias)"""

    model_config = ConfigDict(
        title="資料群",
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
        coerce_numbers_to_str=True,
        populate_by_name=True,
    )

    description: Annotated[
        str | None,
        Field(
            title=_("description").title(),
            default=None,
            json_schema_extra={"multiline": True},
        ),
    ]
    items: Annotated[
        list[T],
        Field(
            title="項目清單",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """Initialize the item group details with custom information.

        It is useful to update details,
        such as adding an alias for better group identification
        while keeping a common setting for easier maintenance.

        If need more type-checkers or model-helpers, continue implementing them in this section.

        .. note::
            Computed fields cannot be sorted by the model itself as they are auto-added after all.
            If extending this model, ensure that any field reordering logic is compatible.

        .. seealso::
            :py:meth:`pydantic.BaseModel.__pydantic_init_subclass__` - https://docs.pydantic.dev/latest/api/base_model

        :param kwargs: Any keyword arguments passed to the class definition that aren't used internally by pydantic.
        """
        super().__pydantic_init_subclass__(**kwargs)
        if cls._items_field_options:
            cls.model_fields.update(
                items=FieldInfo.from_annotation(
                    Annotated[
                        (field_info := cls.model_fields.get("items")).annotation,
                        field_info,
                        Field(**cls._items_field_options),
                    ]
                )
            )
            cls.model_rebuild(force=True)

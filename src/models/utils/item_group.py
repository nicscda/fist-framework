import re
from typing import Annotated, ClassVar, Generic, Mapping, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.fields import FieldInfo

from .validator import duplicate_validator


class Item(BaseModel):
    """資料項目模型，用於統一結構生成。"""

    _pattern: ClassVar[str] = ""
    """ID format, keep empty if no restrictions."""

    model_config = ConfigDict(
        title="資料項",
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
            title="編號",
            min_length=1,
            max_length=100,
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            title="說明",
            default=None,
            allow_multiple_lines=True,
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
            id=FieldInfo.merge_field_infos(
                cls.model_fields.get("id"),
                FieldInfo.from_annotation(
                    Annotated[
                        str,
                        StringConstraints(
                            to_upper=True,
                            pattern=(
                                re.compile(cls._pattern, re.IGNORECASE)
                                if cls._pattern
                                else None
                            ),
                        ),
                    ]
                ),
            )
        )
        cls.model_rebuild(force=True)


T = TypeVar("T", bound=Item, covariant=True)


class Group(BaseModel, Generic[T]):
    """資料群組模型，用於統一結構生成。"""

    _items_info: ClassVar[Mapping] = {}
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
            title="說明",
            default=None,
            allow_multiple_lines=True,
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
        if cls._items_info:
            cls.model_fields.update(
                items=FieldInfo.merge_field_infos(
                    cls.model_fields.get("items"),
                    **cls._items_info,
                )
            )
            cls.model_rebuild(force=True)

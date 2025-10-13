import re
from operator import attrgetter
from typing import Annotated, ClassVar, override

from pydantic import Field, PrivateAttr, ValidationInfo, field_validator
from pydantic_core import PydanticCustomError

from .config import Config
from .external_reference import ExternalReference
from .item_group import Item
from .validator import duplicate_validator


class Base(Item, title="基本資訊"):
    """基礎資料模型，用於實現紀錄通用類別資料的欄位和方法"""

    _config: Annotated[Config, PrivateAttr(default_factory=Config)]
    """Custom configuration for setting basic properties and information."""
    _folder: ClassVar[str]
    """Folder name of data group, using the plural form of the category as default."""
    _type: ClassVar[str]
    """Category type, using the model class name as default."""

    name: Annotated[
        str,
        Field(
            title="名稱",
            min_length=1,
            max_length=100,
        ),
    ]
    external_references: Annotated[
        list[ExternalReference],
        Field(
            title="外部參考",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]
    contributors: Annotated[
        list[str],
        Field(
            title="貢獻者",
            default_factory=list,
            max_length=100,
        ),
        duplicate_validator,
    ]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._type = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cls.__name__).lower()
        cls._folder = cls._type + "s"

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
        fields = cls.model_fields.copy()
        top = {_: fields.pop(_) for _ in ["id", "name"]}
        bottem = {_: fields.pop(_) for _ in ["external_references", "contributors"]}
        for _ in range(len(cls.model_fields)):
            cls.model_fields.popitem()
        else:
            cls.model_fields.update(**(top | fields | bottem))
            cls.model_rebuild(force=True)

    @property
    def filepath(self):
        return self._config.subfolder_path.joinpath(f"{self._folder}/{self.id}.md")

    @property
    def url(self):
        return f"{self._config.base_url}/{self._config.safe_subfolder(self._folder, self.id)}"

    @field_validator("id", "name")
    @classmethod
    def check_unique_keys(cls, value, info: ValidationInfo):
        if (
            isinstance(info.context, dict)
            and isinstance(table := info.context.get("table"), list)
            and any(_.__dict__[info.field_name] == value for _ in table)
        ):
            raise PydanticCustomError("duplicate_entry", "Duplicate entry not allowed")

        return value

    @field_validator("external_references", mode="before")
    @classmethod
    def sanitize_relative_urls(cls, values: list[dict], info: ValidationInfo):
        if isinstance(info.context, dict) and isinstance(
            config := info.context.get("config"), Config
        ):
            for value in values:
                if (
                    value.get("source_name") == config.source
                    and isinstance(url := value.get("url"), str)
                    and isinstance(external_id := value.get("external_id"), str)
                    and (_ := re.match(rf"^\/[a-z_-]+\/{external_id}$", url))
                ):
                    value.update(url=f"{config.base_url}/{config.safe_subfolder(url)}")

        return values

    @classmethod
    def auto_id(cls, table: list, *, start=1, end=9999):
        if table := sorted(table, key=attrgetter("id")):
            return re.sub(
                r"^[0-9]+$|(?<=[^0-9])[0-9]+$",
                lambda _: str(min(1 + int(_[0]), end)).zfill(len(_[0])),
                getattr(table[-1], "id"),
            )

        return (
            re.sub(
                r"(?P<dot>\\\.)|\[0-9\]\{(?:[0-9]+,)?(?P<num>[0-9]+)\}|[^A-Z]+",
                lambda _: (
                    str(start).zfill(int(__))
                    if (__ := _.group("num"))
                    else "." if _.group("dot") else ""
                ),
                cls._pattern,
            )
            if re.search(r"\[0-9\]\{(?:[0-9]+,)?(?P<num>[0-9]+)\}", cls._pattern)
            else cls._type[:2].upper() + str(start).zfill(len(str(end)))
        )

    @override
    def model_post_init(self, __context):
        super().model_post_init(__context)
        if isinstance(__context, dict) and isinstance(
            config := __context.get("config"), Config
        ):
            self._config = config
            for idx, _ in enumerate(self.external_references):
                if self.url == str(_.url) or (
                    self._config.source == _.source_name and self.id == _.external_id
                ):
                    raise PydanticCustomError(
                        "self_referral",
                        f"Self-referral (external_references.{idx}) not allowed",
                    )
            else:
                self.external_references.insert(
                    0,
                    ExternalReference(
                        source_name=self._config.source,
                        url=self.url,
                        external_id=self.id,
                    ),
                )

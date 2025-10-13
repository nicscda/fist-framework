from typing import Annotated, Iterable

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    model_validator,
)


class ExternalReference(BaseModel):
    """外部參考資料模型，用於紀錄本框架引用資料的來源出處與附錄資訊。"""

    model_config = ConfigDict(
        title="外部參考",
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
    )

    source_name: Annotated[
        str,
        Field(
            title="來源名稱",
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
    url: Annotated[
        AnyHttpUrl | None,
        Field(
            title="網址",
            default=None,
        ),
    ]
    external_id: Annotated[
        str | None,
        Field(
            title="外部編號",
            default=None,
            pattern=r"^[a-zA-Z0-9._-]{1,100}$",
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def least_one(cls, values: dict, info: ValidationInfo):
        include = [k for k, v in cls.model_fields.items() if not v.is_required()]
        if isinstance(info.context, dict):
            if isinstance(_ := info.context.get("include"), Iterable):
                include = list(_)
            if isinstance(_ := info.context.get("exclude"), Iterable):
                include = list(set(include) - set(_))
        if include and all(
            values.get(k) is None and k in include
            for k, v in cls.model_fields.items()
            if not v.is_required()
        ):
            raise ValueError(
                "At least one of the "
                + " or ".join(
                    (sep := ", ").join(f"{_!r}" for _ in include).rsplit(sep, 1)
                )
                + " fields must have a value"
            )
        return values

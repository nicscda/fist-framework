from gettext import gettext as _
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FieldSerializationInfo,
    HttpUrl,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    field_serializer,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

from ...utils.config import get_settings


class ExternalReference(BaseModel):
    """外部參考資料模型，用於紀錄本框架引用資料的來源出處與附錄資訊。"""

    model_config = ConfigDict(
        title=_("external reference").title(),
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
        coerce_numbers_to_str=True,
    )

    source_name: Annotated[
        str,
        Field(
            title=_("source name").title(),
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
    url: Annotated[
        HttpUrl | None,
        Field(
            title=_("url").title(),
            default=None,
        ),
    ]
    external_id: Annotated[
        str | None,
        Field(
            title=_("external id").title(),
            default=None,
            pattern=r"^[a-zA-Z0-9._-]{1,100}$",
        ),
    ]

    @model_validator(mode="before")
    @classmethod
    def least_one(cls, values: dict, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("skip_model_validation")
        ):
            include = [k for k, v in cls.model_fields.items() if not v.is_required()]
            if include and not any(values.get(k) for k in include):
                raise ValueError(
                    "At least one of the "
                    + " or ".join(
                        (sep := ", ")
                        .join(f"{field!r}" for field in include)
                        .rsplit(sep, 1)
                    )
                    + " fields must have a value"
                )

        return values

    @model_validator(mode="before")
    @classmethod
    def resolve_url(cls, values: dict, info: ValidationInfo):
        if (
            not (
                isinstance(info.context, dict)
                and info.context.get("skip_model_validation")
            )
            and isinstance(url := values.get("url"), str)
            and url.startswith("/")
            and (_settings := get_settings()).project_name == values.get("source_name")
        ):
            if not url.endswith(str(values.get("external_id") or "")):
                raise ValidationError.from_exception_data(
                    getattr(info.config, "title", cls.__name__),
                    [
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "url_mismatch",
                                "Relative URL must end with the same external ID.",
                            ),
                            loc=("url",),
                            input=url,
                        )
                    ],
                )

            values.update(url=_settings.get_url_path(url, full=True))

        return values

    @field_serializer("url", mode="wrap", when_used="json")
    def serialize_url(
        self,
        url: HttpUrl | None,
        handler: SerializerFunctionWrapHandler,
        info: FieldSerializationInfo,
    ):
        if (
            isinstance(rendered := handler(url, info), str)  # type: ignore[arg-type]
            and isinstance(info.context, dict)
            and info.context.get("as_relative_url")
            and (_settings := get_settings()).project_name == self.source_name
            and rendered.startswith(base_url := str(_settings.base_url))
        ):
            return "/" + rendered.removeprefix(base_url).strip("/")
        else:
            return rendered

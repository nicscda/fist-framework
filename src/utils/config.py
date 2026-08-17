import os
import re
import tomllib
import urllib.parse
from functools import lru_cache
from gettext import bindtextdomain
from gettext import gettext as _
from gettext import textdomain
from importlib.metadata import metadata, version
from pathlib import Path
from typing import Annotated, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    EmailStr,
    Field,
    HttpUrl,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .functions import get_display_path, sanitize_path, to_snake_case


def _get_package_info() -> tuple[str, str, bool]:
    """Get package name and version from metadata or pyproject.toml."""
    pkg = (__package__ or __name__).split(".")[0]
    try:
        return metadata(pkg)["Name"], version(pkg), False
    except Exception:
        pass
    try:
        with open(Path(__file__).parents[2] / "pyproject.toml", "rb") as f:
            project = tomllib.load(f)["project"]
            return project["name"], project["version"] + "+dev", True
    except Exception:
        return pkg, "0.0.0+dev", True


PACKAGE_NAME, VERSION, IS_DEV = _get_package_info()
ENV_VAR_PREFIX = to_snake_case(PACKAGE_NAME).upper()


class AuthorInformation(BaseModel):

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
        coerce_numbers_to_str=True,
    )

    alias: Annotated[
        str | None,
        StringConstraints(
            to_upper=True,
            min_length=1,
            max_length=100,
            pattern=re.compile(r"^[A-Z0-9_]{1,100}$", re.IGNORECASE),
        ),
        Field(
            default=None,
        ),
    ]
    """Shortened Name.

    It is recommended to use the same identifier as the SDO data.
    """
    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
        ),
    ]
    email: Annotated[
        EmailStr | None,
        Field(
            default=None,
        ),
    ]


class Settings(BaseSettings):
    """Configuration-related Settings."""

    model_config = SettingsConfigDict(
        title=_("configuration").title(),
        extra="ignore",
        str_strip_whitespace=True,
        str_max_length=1000,
        validate_assignment=True,
        frozen=True,
        coerce_numbers_to_str=True,
        env_prefix=ENV_VAR_PREFIX + "_",
        env_file=".env",
        env_ignore_empty=True,
        env_nested_delimiter="_",
        nested_model_default_partial_update=True,
        yaml_file=Path(__file__).parents[1] / "config.yml",
        yaml_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(
                settings_cls,
                *(
                    cast(InitSettingsSource, init_settings).init_kwargs.pop(
                        k, cls.model_config[k]
                    )
                    for k in ("yaml_file", "yaml_file_encoding")
                ),
            ),
        )

    project_name: Annotated[
        str,
        Field(
            default=PACKAGE_NAME.upper(),
            min_length=1,
            max_length=100,
            pattern=r"^[a-zA-Z0-9]+(?:[ ._-]+[a-zA-Z0-9]+)*$",
        ),
    ]
    """Project Title.

    Used as both a source label and a unique identifier (e.g., a custom property of an SDO).

    Must be alphanumeric, allowing spaces, dots, underscores, and dashes between words.
    It is intended to be human-readable, but may be converted to a specific naming convention as needed.
    """
    base_url: Annotated[
        HttpUrl,
        Field(),
    ]
    locale_dir: Annotated[
        DirectoryPath,
        Field(
            default=get_display_path(
                Path(__file__).parents[2 if IS_DEV else 1] / "i18n",
            ),
        ),
    ]
    textdomain: Annotated[
        str,
        Field(
            pattern=r"\w{1,100}$",
            default_factory=textdomain,
        ),
    ]
    output_dir: Annotated[
        DirectoryPath,
        Field(
            default="out",
        ),
    ]
    artifact: Annotated[
        str,
        Field(
            default="bundle.json",
            min_length=1,
            max_length=100,
            pattern=r"^[a-zA-Z0-9]+(?:[/ ._-]+[a-zA-Z0-9]+)*$",
        ),
    ]
    subfolder: Annotated[
        str | None,
        Field(
            default=None,
            min_length=0,
            max_length=100,
            pattern=r"^[a-zA-Z0-9]+(?:[/ ._-]+[a-zA-Z0-9]+)*$",
        ),
    ]
    author: Annotated[
        AuthorInformation,
        Field(
            default=None,
        ),
    ]
    debug: Annotated[
        bool,
        Field(
            default=IS_DEV,
        ),
    ]
    language: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias="language",
        ),
    ]

    @property
    def artifact_path(self):
        """Relative path to artifact based on `output-dir`."""
        return self.output_dir / self.artifact

    @property
    def subfolder_path(self):
        """Relative path to subfolder based on `output-dir`."""
        return self.output_dir / (self.subfolder or "")

    @field_validator("base_url", mode="before")
    @classmethod
    def trailing_slash(cls, value):
        if isinstance(value, str) and not value.endswith("/"):
            return value + "/"
        return value

    @field_validator("output_dir", mode="before")
    @classmethod
    def resolve_path(cls, value):
        if isinstance(value, (str, os.PathLike)):
            Path(value).mkdir(parents=True, exist_ok=True)

        return value

    @model_validator(mode="after")
    def resolve_subpath(self, info: ValidationInfo):
        line_errors = []
        if (path := self.artifact_path).exists() and not path.is_file():
            line_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "path_not_file",
                        "Path does not point to a file",
                    ),
                    loc=("artifact",),
                    input=path.as_posix(),
                )
            )
        if (path := self.subfolder_path).exists() and not path.is_dir():
            line_errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        "path_not_directory",
                        "Path does not point to a directory",
                    ),
                    loc=("subfolder",),
                    input=path.as_posix(),
                )
            )
        if line_errors:
            raise ValidationError.from_exception_data(
                getattr(info.config, "title", type(self).__name__), line_errors
            )

        return self

    def get_url_path(self, *parts: str, full=False):
        """Join and sanitize subpath segments located under the `subfolder`.

        Examples
        ---
        .. code-block:: python
            settings = get_settings()
            assert settings.get_url_path("phases", "P0001") == "phases/P0001"
            settings = init_settings(subfolder="wiki/")
            assert settings.get_url_path("/phases/", "..") == "wiki/phases"

        :param parts: Path segments that form the subpath.
        :param full: Whether to include the domain (base URL) in the result.
        :returns: A sanitized relative subpath as a string.
        """
        path = urllib.parse.quote(sanitize_path(self.subfolder or "", *parts))
        return (self.base_url.encoded_string() + path) if full else path

    def get_file_path(self, *parts: str):
        """Join and sanitize subpath segments located under the `subfolder`.

        :param parts: Path segments that form the subpath.
        :returns: A sanitized relative subpath as a path object.
        """
        return self.subfolder_path / sanitize_path(*parts)


@lru_cache(maxsize=1)
def get_settings():
    """Return the cached Settings instance, creating it on first use."""
    global _current_settings
    if _current_settings is None:
        _current_settings = init_settings()
    return _current_settings


def init_settings(**kwargs):
    """(Re)create the global settings instance manually with optional overrides.

    :param kwargs: Manual control inputs.
    """
    global _current_settings
    _current_settings = Settings(**kwargs)
    if _current_settings.language:
        os.environ.update(LANGUAGE=_current_settings.language)
    bindtextdomain(_current_settings.textdomain, _current_settings.locale_dir)
    get_settings.cache_clear()
    return _current_settings


_current_settings: Settings | None = None


init_settings()

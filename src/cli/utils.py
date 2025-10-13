import functools
import re
import shutil
from gettext import gettext
from pathlib import Path
from typing import Callable, cast

import click
from pydantic_core import Url


class UrlStringParamType(click.types.StringParamType):
    name = "url"

    def convert(self, value, param, ctx):
        try:
            url = Url(super().convert(value, param, ctx))
        except Exception:
            self.fail(
                gettext(f"{value!r} is not a valid url."),
                param,
                ctx,
            )
        else:
            if url.scheme not in ("http", "https"):
                self.fail(
                    gettext(f"{value!r} scheme should be 'http' or 'https'."),
                    param,
                    ctx,
                )
            elif 2048 < len(str(url)):
                self.fail(
                    gettext("Maximum length of the URL is 2048 characters."),
                    param,
                    ctx,
                )
            else:
                return str(url).rstrip("/")


URL_STRING = UrlStringParamType()


def add_comment(message: object, prefix: str = "\n", suffix: str = "\n"):
    """Add message in comment block based on dynamic terminal size.

    :param message: The message about comment content. Other objects are converted to strings.
    :param prefix: Add a newline before the comment block as default.
    :param suffix: Add a newline after the comment block as default.
    """
    if not isinstance(message, str):
        message = str(message)  # Auto-converted if input not string
    if message.strip():
        hr = "-" * shutil.get_terminal_size(fallback=(120, 60)).columns
        return f"{prefix}{hr}\n{message}\n{hr}{suffix}"
    else:
        return ""


def as_default(ctx: click.Context, param: click.Option, value):
    """Callback to replace with default if input is empty."""
    return (
        param.default
        if value is None
        else value.strip() or param.default or "" if isinstance(value, str) else value
    )


def as_uppercase(ctx: click.Context, param: click.Option, value: str):
    """Callback to verify source name format and convert to uppercase."""
    if not re.match(_ := r"^[a-zA-Z0-9_]{1,100}$", value):
        raise click.BadParameter(f"String {value!r} not match pattern '{_}'.")
    return value.upper()


def as_subfile(ctx: click.Context, param: click.Option, value: str):
    """Callback to resolve sub file path based on `target-directory`."""
    if not value.endswith(".json"):
        value += ".json"

    if not ((name := click.format_filename(value)) and 1 <= len(value) <= 100):
        raise click.BadParameter(
            f"File name {name!r} must be between 1 and 100 characters."
        )
    elif not re.match(pattern := r"^[a-zA-Z0-9]+(?:[/._-][a-zA-Z0-9]+)*\.json$", value):
        raise click.BadParameter(
            f"File name {name!r} must be match pattern '{pattern}'."
        )
    else:
        if 1 < len(_ := value.split("/", 1)):
            _[0] += cast(str, ctx.params.get("suffix", ""))
            value = "/".join(_)
        elif len(_ := value.rsplit(".", 1)):
            _[0] += cast(str, ctx.params.get("suffix", ""))
            value = ".".join(_)

        target_directory = cast(Path, ctx.params.get("target_directory"))
        path = target_directory.joinpath(value)
        if not path.is_relative_to(target_directory):
            dirname = click.format_filename(target_directory)
            raise click.BadParameter(
                f"File {name!r} must be within the target directory {dirname!r}."
            )
        elif path.is_dir():
            raise click.BadParameter(f"File {name!r} is a directory.")
    return value


def as_subdir(ctx: click.Context, param: click.Option, value: str):
    """Callback to resolve sub folder path based on `target-directory`."""
    if value:
        if not (name := click.format_filename(value)) and not 1 <= len(value) <= 100:
            raise click.BadParameter(
                f"Directory name {name!r} must be between 1 and 100 characters."
            )
        elif not re.match(pattern := r"^[a-zA-Z0-9]+(?:[/._-][a-zA-Z0-9]+)*$", value):
            raise click.BadParameter(
                f"Directory name {name!r} must be match pattern '{pattern}'."
            )
        else:
            if len(_ := value.split("/", 1)):
                _[0] += cast(str, ctx.params.get("suffix", ""))
                value = "/".join(_)

    target_directory = cast(Path, ctx.params.get("target_directory"))
    path = target_directory.joinpath(value)
    if not path.is_relative_to(target_directory):
        click.echo(f"{path=}")
        dirname = click.format_filename(target_directory)
        raise click.BadParameter(
            f"Directory {name!r} must be within the target directory {dirname!r}."
        )
    elif path.is_file():
        raise click.BadParameter(f"Directory {name!r} is a file.")
    return value


def combine_callbacks(*callbacks: Callable):
    return lambda ctx, param, value: functools.reduce(
        lambda v, cb: cb(ctx, param, v), callbacks, value
    )

import re
import shutil
import traceback
from functools import reduce, wraps
from gettext import gettext as _
from pathlib import Path
from typing import Callable, cast

import click
from pydantic_core import Url

from ..utils.config import Settings, get_settings, init_settings


class SupportsFileType(click.types.Path):

    def __init__(
        self,
        *extensions: str,
        exists=True,
        writable=False,
        readable=True,
        resolve_path=False,
        allow_dash=False,
        path_type=Path,
        executable=False,
    ):
        super().__init__(
            exists=exists,
            dir_okay=False,
            writable=writable,
            readable=readable,
            resolve_path=resolve_path,
            allow_dash=allow_dash,
            path_type=path_type,
            executable=executable,
        )
        self.extensions = extensions

    def convert(self, value, param, ctx):
        if Path(rv := super().convert(value, param, ctx)).suffix not in self.extensions:
            self.fail(
                _(
                    "{filename!r} is not a supported file type. Expected formats: {extensions}."
                ).format(
                    filename=click.format_filename(value),
                    extensions=", ".join(self.extensions),
                ),
                param,
                ctx,
            )
        else:
            return rv


class UrlStringParamType(click.types.StringParamType):

    name = "url"

    def convert(self, value, param, ctx):
        try:
            url = Url(super().convert(value, param, ctx))
        except Exception:
            self.fail(
                _("{value!r} is not a valid url.").format(value=value),
                param,
                ctx,
            )
        else:
            if url.scheme not in ("http", "https"):
                self.fail(
                    _("Scheme should be 'http' or 'https'."),
                    param,
                    ctx,
                )
            elif 2048 < len(str(url)):
                self.fail(
                    _("Maximum length of the URL is 2048 characters."),
                    param,
                    ctx,
                )
            else:
                return url


URL_STRING = UrlStringParamType()


def add_comment(message, prefix: str = "\n", suffix: str = ""):
    """Add message in comment block based on dynamic terminal size.

    If the input is not a string, it will be auto-converted using :py:meth:`str`.
    If in debugging mode and input exception, print a formatted stack trace and exception information.

    :param message: Message about comment content. Other objects are converted to strings.
    :param prefix: Something placed before the comment. Defaults to a newline.
    :param suffix: Something placed after the comment. Defaults to an empty.
    """
    if isinstance(message, Exception) and get_settings().debug:
        message = "".join(traceback.format_exception(message))
    elif not isinstance(message, str):
        message = str(message)

    hr = "-" * shutil.get_terminal_size(fallback=(120, 60)).columns
    return f"{prefix}{hr}\n{message}\n{hr}{suffix}" if message else ""


def as_subfile(*extensions: str):
    """Wrap callback to resolve a file path relative to `--output-dir`.

    :param extensions: File extensions to filter by (e.g., '.json', '.yaml').
    :returns: Click callback that adjusts the file path.
    """

    def _wrap(ctx: click.Context, param: click.Parameter, value: str | None):
        """Resolve a file path relative to `--output-dir`."""
        if value is None:
            return value
        elif not (
            (filename := click.format_filename(value))
            and (min_length := 1) <= len(value) <= (max_length := 100)
        ):
            ctx.fail(
                _(
                    "{name} name {filename!r} must be between {min_length} and {max_length} characters."
                ).format(
                    name=_("file"),
                    filename=filename,
                    min_length=min_length,
                    max_length=max_length,
                )
            )
        elif not re.match(
            pattern := rf"^[a-zA-Z0-9]+(?:[/ ._-]+[a-zA-Z0-9]+)*(?:{"|".join(extensions)})$",
            value,
        ):
            ctx.fail(
                _("{name} name {filename!r} must be match pattern {pattern!r}.").format(
                    name=_("file"),
                    filename=filename,
                    pattern=pattern,
                )
            )
        else:
            if 1 < len(parts := value.split("/", 1)):
                parts[0] += cast(str, ctx.params.get("suffix", ""))
                value = "/".join(parts)
            elif parts := value.rsplit(".", 1):
                parts[0] += cast(str, ctx.params.get("suffix", ""))
                value = ".".join(parts)

            path = (output_dir := cast(Path, ctx.params.get("output_dir"))) / value
            if not path.is_relative_to(output_dir):
                ctx.fail(
                    _(
                        "{name} {filename!r} must be within the target directory {dirname!r}."
                    ).format(
                        name=_("file"),
                        filename=filename,
                        dirname=click.format_filename(output_dir),
                    )
                )
            elif path.is_dir():
                ctx.fail(
                    _("{name} {filename!r} is a directory.").format(
                        name=_("file"),
                        filename=filename,
                    )
                )
        return value

    return _wrap


def as_subdir(ctx: click.Context, param: click.Parameter | None, value: str | None):
    """Resolve a subfolder path relative to `--output-dir`.

    This is used as a callback to ensure the folder path is correctly joined with the target directory.
    """
    if value is None:
        return value
    elif not (
        (filename := click.format_filename(value))
        and (min_length := 1) <= len(value) <= (max_length := 100)
    ):
        ctx.fail(
            _(
                "{name} name {filename!r} must be between {min_length} and {max_length} characters."
            ).format(
                name=_("directory"),
                filename=filename,
                min_length=min_length,
                max_length=max_length,
            )
        )
    elif not re.match(pattern := r"^[a-zA-Z0-9]+(?:[/ ._-]+[a-zA-Z0-9]+)*$", value):
        ctx.fail(
            _("{name} name {filename!r} must be match pattern {pattern!r}.").format(
                name=_("directory"),
                filename=filename,
                pattern=pattern,
            )
        )
    elif paths := value.split("/", 1):
        paths[0] += cast(str, ctx.params.get("suffix", ""))
        value = "/".join(paths)

    path = (output_dir := cast(Path, ctx.params.get("output_dir"))) / value
    if not path.is_relative_to(output_dir):
        ctx.fail(
            _(
                "{name} {filename!r} must be within the target directory {dirname!r}."
            ).format(
                name=_("directory"),
                filename=filename,
                dirname=click.format_filename(output_dir),
            )
        )
    elif path.is_file():
        ctx.fail(
            _("{name} {filename!r} is a file.").format(
                name=_("directory"),
                filename=filename,
            )
        )
    return value


def combine_callbacks(*callbacks: Callable):
    return lambda ctx, param, value: reduce(
        lambda v, cb: cb(ctx, param, v), callbacks, value
    )


def safe_pass(func: Callable):
    """Decorator for Click command functions to handle common errors gracefully.

    Also ensures the context object is passed as the first argument,
    and merges user-defined options to initialize global settings.

    :param func: The command callback to be wrapped.
    """

    @click.pass_context
    @wraps(func)
    def wrapper(ctx: click.Context, *args, **kwargs):
        try:
            avaliables = Settings.model_fields.keys() | ctx.find_root().params.keys()
            if options := ctx.ensure_object(dict) | {
                k: v for k, v in kwargs.items() if v is not None and k in avaliables
            }:
                if ctx.invoked_subcommand:
                    ctx.obj = options
                else:
                    init_settings(**options)

            return func(ctx, *args, **kwargs)
        except (
            KeyboardInterrupt,
            SystemExit,
            click.ClickException,
            click.exceptions.Abort,
            click.exceptions.Exit,
        ) as e:
            raise e
        except ValueError as e:
            raise click.UsageError(str(e))
        except Exception as e:
            raise click.UsageError(_("Unexpected error occurred.") + add_comment(e))

    return wrapper

import os
from functools import wraps
from gettext import gettext as _
from pathlib import Path
from typing import cast

import click
import yaml

from ..utils.config import ENV_VAR_PREFIX, IS_DEV, PACKAGE_NAME, Settings, get_settings
from ..utils.functions import get_display_path
from .utils import SupportsFileType, safe_pass

_YAML_FILE_ENVVAR = f"{ENV_VAR_PREFIX}_YAML_FILE"


def file_option(use_default=True):
    """Decorator factory for --file option shared across config commands."""

    def decorator(func):
        @click.option(
            "--file",
            type=SupportsFileType(".yaml", ".yml", exists=False),
            default=(
                Path(Settings.model_fields.get("output_dir").get_default()) / "config.yml"  # type: ignore[union-attr]
                if use_default
                else None
            ),
            envvar=_YAML_FILE_ENVVAR if use_default else None,
            allow_from_autoenv=use_default,
            show_envvar=use_default,
            show_default=use_default,
            help=_("Path to custom configuration file"),
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


@click.group(
    help=_(
        "Manage configuration settings\n\n"
        "View, edit, and reset framework configuration files.\n"
        "Configuration can be customized via YAML files or environment variables."
    )
)
@safe_pass
def config(ctx: click.Context, **kwargs):
    pass


@config.command(help=_("List configuration settings"))
@click.option(
    "--default",
    "use_default",
    is_flag=True,
    default=False,
    show_default=True,
    help=_("Show built-in default configuration"),
)
@file_option(use_default=False)
@safe_pass
def list(
    ctx: click.Context,
    use_default: bool,
    file: Path | None,
    **kwargs,
):
    if use_default and file:
        ctx.fail("Cannot use --default with --file")
    elif use_default:
        # Show built-in defaults
        click.secho(
            cast(Path, Settings.model_config["yaml_file"]).read_text(),
            fg="cyan",
        )
    elif file:
        # Show specific file
        click.secho(file.read_text(), fg="cyan")
    else:
        # Show current merged settings (default behavior)
        click.echo(
            "---\n"
            + yaml.dump(
                get_settings().model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        )


@config.command(help=_("Edit configuration file in an editor"))
@file_option()
@safe_pass
def edit(
    ctx: click.Context,
    file: Path,
    **kwargs,
):
    _update_config_file(file, False)


@config.command(help=_("Reset configuration file to defaults"))
@file_option()
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help=_("Overwrite without confirmation"),
)
@safe_pass
def reset(
    ctx: click.Context,
    file: Path,
    force: bool,
    **kwargs,
):
    if file.exists() and not force:
        click.confirm(_("Replace existing configuration file?"), abort=True)

    _update_config_file(file, True)


def _update_config_file(file: Path, use_default: bool):
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch(exist_ok=True)
        use_default = True
    if use_default:
        file.write_text(
            cast(Path, Settings.model_config["yaml_file"]).read_text(),
            encoding="utf-8",
        )

    mtime = os.path.getmtime(file)
    click.edit(
        filename=(path := get_display_path(file)),
        extension=".yml",
    )
    click.secho(
        _(
            "No changes made: {path!r}."
            if not use_default and os.path.getmtime(file) == mtime
            else "Local configuration saved: {path!r}."
        ).format(path=path),
        fg="green",
    )
    click.secho("\nNext Steps:\n", fg="cyan", bold=True)
    click.secho("Option 1: Use CLI option (recommended)", fg="cyan")
    click.echo(
        '{command} --yaml-file "{path}" config\n'.format(
            command=f"python -m {__package__}" if IS_DEV else PACKAGE_NAME,
            path=path,
        )
    )
    click.secho("Option 2: Set environment variable", fg="cyan")
    click.secho("# PowerShell", fg="cyan")
    click.echo(f"$env:{_YAML_FILE_ENVVAR}={path!r}")
    click.secho("# cmd.exe", fg="cyan")
    click.echo(f'set "{_YAML_FILE_ENVVAR}={path}"')
    click.secho("# bash/zsh", fg="cyan")
    click.echo(f"export {_YAML_FILE_ENVVAR}={path!r}\n")

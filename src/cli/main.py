from gettext import gettext as _

import click

from ..utils.config import ENV_VAR_PREFIX, PACKAGE_NAME, VERSION
from .add import add
from .build import build
from .config import config
from .transl import transl
from .utils import URL_STRING, SupportsFileType, safe_pass


@click.group(
    invoke_without_command=True,
    context_settings={
        "auto_envvar_prefix": ENV_VAR_PREFIX,
    },
)
@click.version_option(VERSION, prog_name=PACKAGE_NAME)
@click.option(
    "--env-file",
    "_env_file",
    type=click.Path(exists=True, file_okay=True),
    help=_("Path to environment variables file"),
)
@click.option(
    "--env-file-encoding",
    "_env_file_encoding",
    type=str,
    help=_("Encoding used to read the environment file (e.g., 'utf-8')"),
)
@click.option(
    "--yaml-file",
    type=SupportsFileType(".yaml", ".yml"),
    allow_from_autoenv=True,
    show_envvar=True,
    help=_("Path to custom configuration file"),
)
@click.option(
    "--yaml-file-encoding",
    type=str,
    allow_from_autoenv=True,
    show_envvar=True,
    help=_("Encoding used to read the configuration file (e.g., 'utf-8')"),
)
@click.option(
    "--project-name",
    type=str,
    allow_from_autoenv=True,
    show_envvar=True,
    help=_("Framework identifier"),
)
@click.option(
    "--base-url",
    type=URL_STRING,
    allow_from_autoenv=True,
    show_envvar=True,
    help=_("Base URL of your site"),
)
@click.option(
    "--debug/--no-debug",
    is_flag=True,
    default=None,
    help=_("Enable debug mode"),
)
@click.help_option()
@safe_pass
def cli(ctx: click.Context, **kwargs):
    """A tiny tool for semi-automatic editing the framework."""
    if not ctx.invoked_subcommand and not ctx.resilient_parsing:
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()


cli.add_command(add)
cli.add_command(build)
cli.add_command(config)
cli.add_command(transl)

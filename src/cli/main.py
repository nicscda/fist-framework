import click

from ..utils.common import VERSION
from .add import add
from .build import build


@click.group()
@click.version_option(VERSION)
@click.help_option()
def cli():
    """A tiny tool for semi-automatic editing the framework."""
    pass


cli.add_command(add)
cli.add_command(build)

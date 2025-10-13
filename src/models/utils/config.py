import inspect
import re
from dataclasses import field
from functools import cache, cached_property
from pathlib import Path

import click
from pydantic import dataclasses


def _default_source_name():
    return (
        (_.command.name if not _.parent else _.parent.command.name)
        if (_ := click.get_current_context(silent=True))
        else (
            inspect.getmodule(inspect.stack()[0][0])
            .__name__.split(".", 1)[0]
            .strip("_")
        )
    ).upper()


@dataclasses.dataclass(frozen=True)
class Config:
    """Configuration-related Data Model."""

    source: str = field(default_factory=_default_source_name)
    base_url: str = field(default="http://localhost")
    target_directory: Path = field(default_factory=Path)
    output: str = field(default="")
    subfolder: str = field(default="")

    @cached_property
    def output_path(self):
        """Relative path to output file based on `target-directory`."""
        return self.target_directory.joinpath(self.output)

    @cached_property
    def subfolder_path(self):
        """Relative path to subfolder based on `target-directory`."""
        return self.target_directory.joinpath(self.subfolder)

    @cache
    def safe_subfolder(self, *paths: str):
        """Get safe subfolder path string without whitespaces and removing extra slashes.

        >>> config = Config()
        >>> assert config.safe_subfolder("phases", "", "P0001") == "phases/P0001"
        >>> config = Config(subfolder="wiki/")
        >>> assert config.safe_subfolder("/phases/", " ", "/") == "wiki/phases"

        :param *subpaths: Subpath segments, located under the subfolder
        """
        return "/".join(
            __
            for _ in (self.subfolder,) + paths
            if (__ := re.sub(r"^[ \/]+|[ \/]+$", "", _))
        )

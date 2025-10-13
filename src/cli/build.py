import os
import shutil
import time
from datetime import datetime
from pathlib import Path

import click

from ..utils.common import VERSION, nget
from ..utils.parsing import Parser
from .utils import (
    URL_STRING,
    add_comment,
    as_default,
    as_subdir,
    as_subfile,
    as_uppercase,
    combine_callbacks,
)


@click.command()
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--source",
    envvar="SOURCE",
    required=True,
    type=str,
    help="Source framework name.",
    callback=as_uppercase,
)
@click.option(
    "--base-url",
    envvar="BASE_URL",
    required=True,
    type=URL_STRING,
    help="Base URL of your site.",
)
@click.option(
    "-R",
    "-r",
    "--recursive",
    is_flag=True,
    help="Search recursively in subdirectories.",
)
@click.option(
    "--clean",
    "auto_clean",
    envvar="AUTO_CLEAN",
    is_flag=True,
    help="Remove existing outputs first.",
)
@click.option(
    "-t",
    "--target-directory",
    type=click.Path(exists=True, file_okay=False, writable=True, path_type=Path),
    default="out",
    show_default=True,
    is_eager=True,
    help="Directory to save generated files.",
)
@click.option(
    "-o",
    "--output",
    envvar="OUTPUT",
    type=str,
    show_default=True,
    default="bundle.json",
    help="Archive name of STIX bundle file.",
    callback=combine_callbacks(as_default, as_subfile),
)
@click.option(
    "--subfolder",
    "subfolder",
    envvar="SUBFOLDER",
    type=str,
    show_default=True,
    default="",
    help="Subfolder path of web pages.",
    callback=combine_callbacks(as_default, as_subdir),
)
@click.option(
    "--suffix",
    envvar="SUFFIX",
    type=click.Choice(["date", "timestamp", "version"]),
    is_eager=True,
    help="Automatically add suffixes to output root files and folders.",
    callback=lambda ctx, param, value: str(
        datetime.today().strftime("--%Y-%m-%d")
        if "date" == value
        else (
            f"--{datetime.today().timestamp():.0f}"
            if "timestamp" == value
            else f"--{VERSION}" if "version" == value else ""
        )
    ),
)
def build(
    paths: list[Path],
    auto_clean: bool,
    recursive: bool,
    target_directory: Path,
    **kwargs,
):
    """Generate custom framework documents

    Import data with specified file extensions, then export documentation including bundle.
    Supported formats: .json, .yaml.
    """
    try:
        if not paths:
            raise click.UsageError("At least one path must be provided.")
        else:
            if auto_clean:
                with os.scandir(target_directory) as entries:
                    for entry in entries:
                        if entry.is_file():
                            os.unlink(entry.path)
                        else:
                            shutil.rmtree(entry.path)
                    else:
                        click.secho(
                            f"All files and directories in '{target_directory.absolute()}' deleted successfully.",
                            blink=True,
                            bold=True,
                        )

            click.secho("Loading data files...", blink=True, bold=True)
            parser = Parser(target_directory=target_directory, **kwargs)
            parser.bundle.import_data_files(
                paths,
                recursive,
                error_callback=_error_callback,
                count_callback=_count_callback,
            )
            start_time = time.time()
            click.secho(
                f"Output saved to '{os.path.relpath(parser.to_stix(), os.getcwd())}' "
                f"(Elapsed: {time.time() - start_time:,.2f} sec)",
                blink=True,
                bold=True,
            )
            for filepath, s in parser.to_markdown():
                if filepath:
                    filepath.parent.mkdir(exist_ok=True, parents=True)
                    with open(filepath, "w", encoding="utf-8") as file:
                        file.write(s)
            else:
                click.secho(
                    f"Full documentation saved to '{os.path.relpath(parser.bundle.subpath().parent, os.getcwd())}'",
                    blink=True,
                    bold=True,
                )

    except (KeyboardInterrupt, SystemExit):
        pass
    except (
        click.ClickException,
        click.exceptions.Abort,
        click.exceptions.Exit,
    ) as e:
        raise e
    except Exception as e:
        raise click.UsageError(
            click.style("Unexpected error occurred.", fg="red") + add_comment(e)
        )


def _error_callback(filepath, e):
    raise click.UsageError(
        click.style(f"Invalid '{filepath}' file.", fg="red") + add_comment(e)
    )


def _count_callback(total: int, field_name: str | None = None):
    if not field_name:
        if total:
            click.secho(
                f"\nTotal: {nget(total, "imported entity", "imported entities", nformat=",")}\n",
                blink=True,
                bold=True,
            )
        else:
            raise click.UsageError("No file with supported extension found.")
    else:
        click.secho(
            f"Importing {nget(total, field_name.replace("_", " ").removesuffix("s"), nformat=",")} ...",
            fg="green",
        )

from datetime import datetime
from gettext import gettext as _
from gettext import ngettext
from pathlib import Path
from typing import cast

import click

from ..models import LEGAL_FILE_EXTENSIONS, Manifest
from ..utils.config import VERSION, Settings
from ..utils.functions import clear_dir, get_display_path, timeit
from ..utils.parsing import Parser
from .utils import add_comment, as_subdir, as_subfile, combine_callbacks, safe_pass


@click.command(
    help=_(
        "Generate custom framework documents\n\n"
        "Import data files and export documentation with STIX bundle.\n"
        "Supported formats: {extensions}."
    ).format(extensions=", ".join(LEGAL_FILE_EXTENSIONS))
)
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-R",
    "-r",
    "--recursive",
    is_flag=True,
    help=_("Search recursively in subdirectories"),
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=Settings.model_fields.get("output_dir").get_default(),  # type: ignore[union-attr]
    show_default=True,
    is_eager=True,
    help=_("Directory to save outputs"),
)
@click.option(
    "--clean/--no-clean",
    "auto_clean",
    is_flag=True,
    default=False,
    show_default=True,
    help=_("Remove existing outputs first"),
)
@click.option(
    "-o",
    "--output",
    "artifact",
    type=str,
    help=_("STIX bundle output filename"),
    callback=combine_callbacks(
        lambda ctx, param, value: (
            Settings.model_fields.get("artifact").get_default()  # type: ignore[union-attr]
            if not value and cast(click.Context, ctx).params.get("suffix", "")
            else value
        ),
        as_subfile(".json"),
    ),
)
@click.option(
    "--subfolder",
    type=str,
    help=_("Output subdirectory and URL subpath (empty for root)"),
    callback=as_subdir,
)
@click.option(
    "--suffix",
    type=click.Choice(["date", "timestamp", "version"]),
    is_eager=True,
    help=_("Add suffix to outputs"),
    callback=lambda ctx, param, value: (
        datetime.today().strftime("--%Y-%m-%d")
        if "date" == value
        else (
            f"--{datetime.today().timestamp():.0f}"
            if "timestamp" == value
            else f"--{VERSION.replace("+", ".")}" if "version" == value else ""
        )
    ),
)
@safe_pass
def build(
    ctx: click.Context,
    paths: list[Path],
    recursive: bool,
    output_dir: Path,
    auto_clean: bool,
    **kwargs,
):
    if not paths:
        ctx.fail(_("At least one path must be provided."))
    elif auto_clean:
        clear_dir(output_dir)
        click.secho(
            _("All files and directories in {path!r} deleted successfully.").format(
                path=get_display_path(output_dir)
            ),
            blink=True,
            bold=True,
        )

    with timeit(click.echo):
        click.secho(_("Loading data files..."), blink=True, bold=True)
        parser = Parser(
            Manifest(
                paths,
                recursive,
                lambda path, e: ctx.fail(
                    _("{value!r} is not a valid file.").format(value=path.as_posix())
                    + add_comment(e)
                ),
                lambda total, field_name: (
                    click.secho(
                        ngettext(
                            "Importing 1 {unit}...",
                            "Importing {total:,} {unit}s...",
                            total,
                        ).format(
                            total=total,
                            unit=_(field_name.replace("_", " ").removesuffix("s")),
                        ),
                        fg="green",
                    )
                    if field_name
                    else (
                        click.secho(
                            "\n"
                            + ngettext(
                                "Total: 1 imported entity",
                                "Total: {total:,} imported entities",
                                total,
                            ).format(total=total)
                            + "\n",
                            blink=True,
                            bold=True,
                        )
                        if total
                        else ctx.fail(
                            _(
                                "No supported files found. Expected formats: {extensions}."
                            ).format(extensions=", ".join(LEGAL_FILE_EXTENSIONS))
                        )
                    )
                ),
            ),
        )
        click.echo(
            _("STIX bundle saved to {path!r}").format(
                path=get_display_path(parser.to_stix())
            )
        )
        click.echo(
            _("Full documentation exported to {path!r}").format(
                path=get_display_path(parser.to_json())
            )
        )

import os
import re
import shutil
import subprocess
from gettext import gettext as _
from pathlib import Path
from tempfile import NamedTemporaryFile

import click

from ..utils.config import PACKAGE_NAME, VERSION, Settings, get_settings
from ..utils.functions import get_display_path, load_files
from .utils import safe_pass


@click.command(
    help=_(
        "Manage translation files\n\n"
        "Generate and compile translation files using GNU gettext.\n"
        "Extracts translatable strings from source code and creates PO/MO files."
    )
)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, file_okay=False, writable=True, path_type=Path),
    default=Settings.model_fields.get("locale_dir").get_default(),  # type: ignore[union-attr]
    show_default=True,
    help=_("Directory to save outputs"),
)
@click.option(
    "--build/--no-build",
    "auto_build",
    is_flag=True,
    default=False,
    show_default=True,
    help=_("Generate PO files from source code folder"),
)
@click.option(
    "--compile/--no-compile",
    "auto_compile",
    is_flag=True,
    default=True,
    show_default=True,
    help=_("Convert PO to MO files"),
)
@safe_pass
def transl(
    ctx: click.Context,
    output_dir: Path,
    auto_build: bool,
    auto_compile: bool,
    **kwargs,
):
    _settings = get_settings()
    if missing := [
        cmd for cmd in ("xgettext", "msginit", "msgfmt") if not shutil.which(cmd)
    ]:
        ctx.fail(
            _(
                "Missing tools: {tools}\n"
                "Please install GNU gettext (e.g., `apt install gettext`, `brew install gettext`).\n"
                "See: {url}"
            ).format(
                tools=", ".join(missing), url="https://www.gnu.org/software/gettext"
            ),
        )
    elif not any(output_dir.iterdir()):
        (output_dir / os.environ.get("LANGUAGE", "en_US").split(":")[0]).mkdir(
            parents=True, exist_ok=True
        )

    if auto_build:
        with NamedTemporaryFile("w+", encoding="utf-8", delete_on_close=False) as tmp:
            tmp.write(
                "\n".join(
                    filepath.resolve().as_posix()
                    for filepath in load_files(
                        Path(__file__).parents[1],
                        ".py",
                        recursive=True,
                    )
                )
            )
            tmp.close()
            for path in output_dir.iterdir():
                po = _get_po_filename(path, _settings.textdomain)
                subprocess.run(
                    [
                        "xgettext",
                        f"--copyright-holder={_settings.author.name}",
                        f"--default-domain={_settings.textdomain}",
                        "--from-code=utf-8",
                        f"--files-from={Path(tmp.name).as_posix()}",
                        "--join-existing",
                        "--language=Python",
                        f"--output={po}",
                        f"--msgid-bugs-address={_settings.author.email}",
                        "--no-location",
                        f"--package-name={PACKAGE_NAME}",
                        f"--package-version={VERSION}",
                        "--sort-by-file",
                    ],
                    check=True,
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                )

                subprocess.run(
                    [
                        "msginit",
                        "--no-translator",
                        f"--locale={path.name}",
                        f"--input={po}",
                        f"--output={po}",
                    ],
                    check=True,
                    timeout=10,
                    stderr=subprocess.DEVNULL,
                )
                click.secho(
                    _("Updated {filename!r}.").format(filename=get_display_path(po)),
                    fg="green",
                )
            else:
                click.echo(_("All portable objects buildet!"))
                click.echo(
                    ""
                    if auto_compile
                    else _(
                        "Please remember to update the translations in {filename!r} before compiling."
                    ).format(
                        filename=(
                            output_dir / "**" / f"{_settings.textdomain}.po"
                        ).as_posix()
                    )
                )

    if auto_compile:
        for targetpath in output_dir.iterdir():
            po = _get_po_filename(targetpath, _settings.textdomain)
            mo = re.sub(r"\.po$", ".mo", po, flags=re.IGNORECASE)
            subprocess.run(
                ["msgfmt", po, "-o", mo],
                check=True,
                timeout=10,
                stderr=subprocess.DEVNULL,
            )
            click.secho(
                _("Updated {filename!r}.").format(filename=get_display_path(mo)),
                fg="green",
            )
        else:
            click.echo(_("All translations compiled!"))


def _get_po_filename(locale_dir: Path, domain: str):
    file = locale_dir / "LC_MESSAGES" / f"{domain}.po"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.touch(exist_ok=True)
    return file.resolve().as_posix()

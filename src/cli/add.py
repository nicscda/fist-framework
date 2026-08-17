import re
import shutil
from enum import Enum
from gettext import gettext as _
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, TypeVar, get_origin

import click
from pydantic import BaseModel, create_model

from ..models import Component, Manifest, Technique
from ..utils.config import Settings
from ..utils.functions import fit, next_non_none_type
from .utils import add_comment, safe_pass

T = TypeVar("T")
R = TypeVar("R")


@click.command(
    help=_(
        "Create framework data file\n\n"
        "Interactive prompts guide you through the process."
    )
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
    help=_("Directory to save outputs"),
)
@click.option(
    "--auto-increment/--no-auto-increment",
    is_flag=True,
    default=True,
    show_default=True,
    help=_("Auto-generate a unique number on insert"),
)
@safe_pass
def add(
    ctx: click.Context,
    paths: list[Path],
    recursive: bool,
    output_dir: Path,
    auto_increment: bool,
    **kwargs,
):
    manifest = Manifest(
        paths,
        recursive,
        lambda path, e: ctx.fail(
            _("{value!r} is not a valid file.").format(value=path.as_posix())
            + add_comment(e)
        ),
        context={"exclude_self": True},
    )

    if (
        not (
            __ := _choice_prompt(  # type: ignore[var-annotated]
                _("Please select the type of data you want to create:"),
                manifest.mapping().items(),
                lambda k, v: f"({k}) {v[1].model_json_schema()["title"]}",
            )
        )
        or not isinstance(table := manifest.__dict__[__[0]], list)
        or not isinstance(title := (tp := __[1]).model_json_schema()["title"], str)
    ):
        ctx.fail(_("No model with supported type found."))
    else:
        default_values: dict[str, Any] = {
            "type": (
                _choice_prompt(
                    _("Please select the type of {data!r} you want to create:").format(
                        data=title
                    ),
                    field.annotation,
                    lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",
                ).value
                if (
                    (field := tp.model_fields.get("type"))
                    and isinstance(field.annotation, type)
                    and issubclass(field.annotation, Enum)
                )
                else tp._type
            )
        }

        if auto_increment:

            def _parent_prompt(text: str, _table: list = table) -> str:
                """Ask the relevant parent and return the corresponding child ID."""

                return click.prompt(
                    text,
                    value_proc=lambda parent_id: tp.auto_id(
                        _table,
                        parent_id=_pattern_proc(
                            re.sub(
                                r"(?<=[0-9]\}(?!\$$))(?:.+(?=\$$)|.+(?!\$$))",
                                "",
                                tp._pattern,
                            ),
                            parent_id,
                        ),
                    ),
                    show_default=False,
                )

            match tp._type:
                case Component._type:
                    data_id = _parent_prompt(
                        _("Please enter the detection source ID of it"),
                        table + manifest.detection_sources,
                    )
                case Technique._type:
                    data_id = (
                        _parent_prompt(_("Please enter the parent technical ID of it"))
                        if click.confirm(_("Is it a sub-technique?"))
                        else tp.auto_id(table)
                    )
                case _:
                    data_id = tp.auto_id(table)

            default_values.update(id=data_id)

        entity = tp(
            **default_values,
            **_model_prompt(
                tp,
                [k for k in tp.model_fields.keys() if k not in default_values],
                parent=_("of {data!r}").format(data=title),
                context={"skip_model_validation": True, "table": table},
            ),
        )

        filepath = entity.model_dump_yaml(
            output_dir
            / (
                entity._group
                if recursive or (output_dir / entity._group).is_dir()
                else ""
            ),
            overwrite=True,
        )
        click.echo(
            _(
                "New {data!r} file has been created successfully.\n"
                "Please open {filename!r} to view the content and edit it further."
            ).format(data=title, filename=filepath.as_posix())
        )


def _choice_proc(mapping: dict[int, T], value: str):
    try:
        return mapping[int(value)]
    except Exception:
        raise click.UsageError(
            _("{value!r} is not a valid choice.").format(
                value=fit(value, width=50, fillchar="")
            )
        )


def _choice_prompt(
    text: str,
    options: Iterable[T],
    formatter: Callable[[int, T], str],
    is_required: bool = True,
    default: Any | None = None,
    post_value_proc: Callable[[T], R] | None = None,
) -> T | R:
    mapping = dict(enumerate(options, start=1))
    colspan = (shutil.get_terminal_size(fallback=(120, 60)).columns - 4) // (
        padding := 4 + max(len(formatter(k, v)) for k, v in mapping.items())
    )

    def _post_value_proc(v):
        value = default if "" == v and not is_required else _choice_proc(mapping, v)
        return post_value_proc(value) if callable(post_value_proc) else value

    return click.prompt(
        f"{text}\n{" " * 4}"
        + "".join(
            f"{f"{formatter(k, v)}":{padding}}"
            + ("" if k % colspan else f"\n{" " * 4}")
            for k, v in mapping.items()
        )
        + "\n\n"
        + _("Enter the number corresponding to your choice ({start}-{end})").format(
            start=1, end=len(mapping)
        ),
        default=None if is_required else "",
        value_proc=_post_value_proc,
        show_default=False,
    )


def _model_field_proc(tp: type[BaseModel], key: str, value, context=None):
    try:
        if (
            "" == value
            and (field := tp.model_fields.get(key))
            and not field.is_required()
        ):
            value = field.get_default()
        create_model(  # type: ignore[call-overload]
            tp.__name__ + "_" + key,
            __config__=None,
            __doc__=None,
            __base__=tp,
            __module__=__name__,
            __validators__=None,
            __cls_kwargs__=None,
            __qualname__=None,
            **{
                k: (Optional[v.annotation], None)
                for k, v in tp.model_fields.items()
                if k != key
            },
        ).model_validate({key: value}, context=context)
        return value
    except Exception as e:
        raise click.UsageError(
            _("{value!r} is not a valid value.").format(
                value=fit(
                    value[-1] if isinstance(value, list) and value else value,
                    width=50,
                    fillchar="",
                )
            )
            + add_comment(e)
        )


def _model_prompt(
    tp: type[BaseModel],
    include_fields: Iterable[str] | None = None,
    *,
    parent: str,
    on_success: Callable[..., Any] | None = None,
    context=None,
):
    result = {}
    for k, v in tp.model_fields.items():
        if k not in ("created", "modified", "revoked") and (
            not include_fields or k in include_fields
        ):
            _display_name = v.title or k.title()
            _tp = next_non_none_type(v.annotation)
            _is_type = isinstance(_tp, type)
            if get_origin(v.annotation) in (list, set, tuple):
                if click.confirm(
                    _("Want to add new data to {field!r}?").format(field=_display_name)
                ):
                    items = []  # type: ignore[var-annotated]
                    if _is_type and issubclass(_tp, BaseModel):
                        while True:
                            try:
                                items.append(
                                    _model_prompt(
                                        _tp,
                                        parent=_(
                                            "{field!r} of the No. {num} {parent}"
                                        ).format(
                                            field=_display_name,
                                            num=len(items) + 1,
                                            parent=parent,
                                        ),
                                        on_success=lambda item: _model_field_proc(
                                            tp, k, items + [item], context
                                        ),
                                        context=context,
                                    )
                                )
                            except click.UsageError as e:
                                click.echo(_("Error: {message}").format(message=e))
                            if not click.confirm(
                                _("Continue adding new data to {field!r}?").format(
                                    field=_display_name
                                )
                            ):
                                result[k] = items
                                break
                    elif _is_type and issubclass(_tp, Enum):
                        while True:
                            items = _choice_prompt(
                                _(
                                    "Please select {field!r} of the No. {num} {parent}"
                                ).format(
                                    field=_display_name,
                                    num=len(items) + 1,
                                    parent=parent,
                                ),
                                _tp,
                                lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",  # type: ignore[attr-defined]
                                default="",
                                is_required=False,
                                post_value_proc=lambda value: (
                                    _model_field_proc(tp, k, items + [value], context)
                                    if value
                                    else items + [value]
                                ),
                            )
                            if "" == items[-1]:
                                result[k] = items[:-1]
                                break
                    else:
                        while True:
                            if (v.json_schema_extra or {}).get("multiline"):  # type: ignore[union-attr]
                                click.termui.visible_prompt_func = _multiple_prompt
                            items = click.prompt(
                                _(
                                    "Please enter {field!r} of the No. {num} {parent}"
                                ).format(
                                    field=_display_name,
                                    num=len(items) + 1,
                                    parent=parent,
                                ),
                                default="",
                                value_proc=lambda value: (
                                    _model_field_proc(tp, k, items + [value], context)
                                    if value
                                    else items + [value]
                                ),
                                show_default=False,
                            )
                            click.termui.visible_prompt_func = input
                            if "" == items[-1]:
                                result[k] = items[:-1]
                                break
            elif _is_type and issubclass(_tp, BaseModel):
                result[k] = _model_prompt(
                    _tp,
                    parent=_("{field!r} of {parent}").format(
                        field=_display_name, parent=parent
                    ),
                    on_success=lambda item: _model_field_proc(tp, k, item, context),
                    context=context,
                )
            elif _is_type and issubclass(_tp, Enum):
                result[k] = _choice_prompt(
                    _("Please select {field!r} of {parent}:").format(
                        field=_display_name, parent=parent
                    ),
                    _tp,
                    lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",  # type: ignore[attr-defined]
                    default=None if v.is_required() else v.get_default(),
                    is_required=v.is_required(),
                )
            else:
                if (v.json_schema_extra or {}).get("multiline"):  # type: ignore[union-attr]
                    click.termui.visible_prompt_func = _multiple_prompt
                result[k] = click.prompt(
                    _("Please enter {field!r} of {parent}").format(
                        field=_display_name, parent=parent
                    ),
                    default=None if v.is_required() else "",
                    value_proc=lambda value: _model_field_proc(tp, k, value, context),
                    show_default=False,
                )
                click.termui.visible_prompt_func = input
    else:
        callable(on_success) and on_success(result)
        return result


def _multiple_prompt(prompt_text: object = ""):
    if "|" == (
        value := input(
            prompt_text
            + add_comment(
                _("Supports multi-line text. Press {key!r} to start editing.").format(
                    key="|"
                ),
                suffix="\n",
            )
        )
    ):
        inp = []
        click.echo(
            add_comment(
                _(
                    "Multiline mode is enabled. Press [Enter] twice to submit your entry."
                ),
                prefix="",
            )
        )
        last_is_empty = False
        while (val := input("> ").strip()) or not last_is_empty:
            inp.append(val)
            last_is_empty = not bool(val)
        value = "\n".join(inp) if any(inp) else ""
    return value


def _pattern_proc(pattern: str | re.Pattern, value: str):
    if re.match(pattern, value):
        return value
    else:
        raise click.UsageError(
            _("{value!r} is not a valid format.").format(
                value=fit(value, width=50, fillchar="")
            )
            + add_comment(
                f"String should match pattern {pattern!r} [input_value={value!r}]"
            )
        )

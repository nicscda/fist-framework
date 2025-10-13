import itertools
import re
import shutil
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, TypeVar, cast, get_origin

import click
from pydantic import BaseModel, create_model
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..models import Bundle, Component, Contributor, Technique
from ..utils.common import next_not_none_type, truncate
from .utils import add_comment

T = TypeVar("T", bound=Any)
V = TypeVar("V", bound=Any)


@click.command(deprecated=True)
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
    help="Search recursively in subdirectories.",
)
@click.option(
    "--auto-increment/--no-auto-increment",
    envvar="AUTO_INCREMENT",
    is_flag=True,
    default=True,
    show_default=True,
    help="A unique number to be generated automatically when a new record is inserted.",
)
@click.option(
    "-t",
    "--target-directory",
    type=click.Path(exists=True, file_okay=False, writable=True, path_type=Path),
    default="data",
    show_default=True,
    help="Directory to save generated files.",
)
@click.option(
    "--template",
    type=click.Path(exists=True, path_type=Path),
    default="templates",
    show_default=True,
    help="Template folder or file for loading styles.",
)
def add(
    paths: list[Path],
    recursive: bool,
    auto_increment: bool,
    target_directory: Path,
    template: Path,
    **kwargs,
):
    """Create a data file

    This is a step-by-step guide for beginners to add new framework data.
    """
    try:
        bundle = Bundle(kwargs)
        bundle.import_data_files(paths, recursive)

        if (
            not (
                _ := _choice_prompt(
                    "請選擇想創建的資料類型？",
                    bundle.mapping().items(),
                    lambda k, v: f"({k}) {v[1].model_json_schema()["title"]}",
                )
            )
            or not (tabel_name := _[0])
            or not isinstance(table := bundle.__dict__[tabel_name], list)
            or not (data_model := _[1])
            or not isinstance(title := data_model.model_json_schema()["title"], str)
        ):
            raise RuntimeError("No model with supported type found.")

        default_values: dict[str, Any] = dict(
            type=(
                _choice_prompt(
                    f"請選擇想創建的「{title}」類型？",
                    field.annotation,
                    lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",
                ).value
                if (
                    (field := data_model.model_fields.get("type"))
                    and isinstance(field.annotation, type)
                    and issubclass(field.annotation, Enum)
                )
                else data_model._type
            )
        )
        if auto_increment:

            def _parent_prompt(text: str, _table: list = table) -> str:
                """Ask the relevant parent and return the corresponding child ID."""

                def _parent_proc(parent_id):
                    try:
                        return data_model.auto_id(
                            _table,
                            parent_id=_pattern_proc(
                                re.sub(
                                    r"(?<=[0-9]\}(?!\$$))(?:.+(?=\$$)|.+(?!\$$))",
                                    "",
                                    data_model._pattern,
                                ),
                                parent_id,
                            ),
                        )
                    except click.ClickException as e:
                        raise e
                    except Exception as e:
                        raise click.UsageError(
                            click.style(
                                f"{parent_id!r} is not a valid parent ID.", fg="red"
                            )
                            + add_comment(e)
                        )

                return click.prompt(text, value_proc=_parent_proc, show_default=False)

            match data_model._type:
                case Contributor._type:
                    data_id = data_model.auto_id(
                        table, prefix=data_model._type[0] + default_values["type"][0]
                    )
                case Component._type:
                    data_id = _parent_prompt(
                        "請輸入偵測來源編號", table + bundle.detection_sources
                    )
                case Technique._type:
                    data_id = (
                        _parent_prompt("請輸入上層技術編號")
                        if click.confirm("是否為子技術資料？")
                        else data_model.auto_id(table)
                    )
                case _:
                    data_id = data_model.auto_id(table)

            default_values.update(id=data_id)

        _yaml = YAML()
        _yaml.indent(mapping=2, sequence=4, offset=2)
        _yaml.preserve_quotes = True
        _yaml.explicit_start = True
        match (
            __ := (
                template
                if template.is_file()
                else template.joinpath(
                    (
                        data_model._folder
                        if not data_model._folder.startswith(default_values["type"])
                        else ""
                    ),
                    f"{default_values["type"]}.yaml",
                )
            )
        ).suffix.lower():
            case ".yaml" | ".yml":
                with open(__, "r", encoding="utf-8") as file:
                    commented_map = cast(CommentedMap, _yaml.load(file))
                    if commented_map["type"] != default_values["type"]:
                        raise RuntimeError(
                            f"Template not match the selected type {default_values["type"]!r}."
                        )

                entity = data_model(
                    **default_values,
                    **_model_prompt(
                        data_model,
                        [_ for _ in commented_map.keys() if _ not in default_values],
                        prefix=f"「{title}」的",
                        table=table,
                    ),
                )
            case _:
                raise RuntimeError("Invalid template file.")

        for _ in itertools.count():
            try:
                filepath = target_directory.joinpath(
                    entity._folder,
                    f"{entity.id}{f" ({_})" if _ else ""}.yaml",
                )
                with open(filepath, "x", encoding="utf-8") as file:
                    commented_map.update(
                        **entity.model_dump(
                            mode="json",
                            include=commented_map.keys(),
                            exclude_none=True,
                        ),
                    )
                    _yaml.dump(dict(commented_map), stream=file)

                click.echo(
                    f"成功建立新的「{title}」資料，請打開 '{filepath}' 查看檔案內容與進一步編輯。"
                )
                break
            except FileExistsError:
                if 99 <= _:
                    raise RuntimeError("Too many attempts to create a unique filename.")

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


def _choice_proc(mapping: Mapping[int, T], value: str):
    try:
        return mapping[int(value)]
    except Exception:
        raise click.UsageError(
            click.style(f"{truncate(value)!r} is not a valid choice.", fg="red")
        )


def _choice_prompt(
    text: str,
    options: Iterable[T],
    formatter: Callable[[int, T], str],
    is_required: bool = True,
    default: Any | None = None,
    post_value_proc: Callable[[T], V] = lambda _: _,
) -> V:
    mapping = dict(enumerate(options, start=1))
    colspan = (shutil.get_terminal_size(fallback=(120, 60)).columns - 4) // (
        padding := 4 + max(len(formatter(k, v)) for k, v in mapping.items())
    )
    return click.prompt(
        f"{text}\n{" " * 4}"
        + "".join(
            f"{f"{formatter(k, v)}":{padding}}"
            + ("" if k % colspan else f"\n{" " * 4}")
            for k, v in mapping.items()
        )
        + f"\n請輸入對應的數字 1 到 {len(mapping)}",
        default=None if is_required else "",
        value_proc=lambda _: post_value_proc(
            default if "" == _ and not is_required else _choice_proc(mapping, _)
        ),
        show_default=False,
    )


def _model_field_proc(t: type[BaseModel], key: str, value, **context):
    try:
        if "" == value and (_ := t.model_fields.get(key)) and not _.is_required():
            value = _.get_default()
        create_model(
            t.__name__,
            __config__=None,
            __doc__=None,
            __base__=t,
            __module__=__name__,
            __validators__=None,
            __cls_kwargs__=None,
            **{
                k: (Optional[v.annotation], None)
                for k, v in t.model_fields.items()
                if k != key
            },
        ).model_validate({key: value}, context=context)
        return value
    except Exception as e:
        raise click.UsageError(
            click.style(f"{truncate(value)!r} is not a valid value.", fg="red")
            + add_comment(e)
        )


def _model_prompt(
    t: type[BaseModel],
    include_fields: Iterable[str] | None = None,
    *,
    prefix: str = "",
    callable: Callable[..., Any] = lambda **_: ...,
    **context,
):
    result = {}
    for k, v in t.model_fields.items():
        if include_fields and k not in include_fields:
            continue
        elif get_origin(v.annotation) in (list, set, tuple):
            if click.confirm(f"是否要添加「{v.title or k.title()}」列表項目？"):
                items = []  # type: ignore[var-annotated]
                if isinstance(
                    _t := next_not_none_type(v.annotation), type
                ) and issubclass(_t, BaseModel):
                    while True:
                        try:
                            items.append(
                                _model_prompt(
                                    _t,
                                    prefix=f"{prefix}第 {len(items) + 1} 筆「{v.title or k.title()}」的",
                                    callable=lambda **_: _model_field_proc(
                                        t, k, items + [_], **context
                                    ),
                                    **(context | dict(include=[])),
                                )
                            )
                        except click.UsageError as e:
                            click.echo(f"Error: {e}")
                        finally:
                            if not click.confirm(
                                f"是否繼續添加「{v.title or k.title()}」列表項目？"
                            ):
                                result[k] = items
                                break
                elif isinstance(
                    _t := next_not_none_type(v.annotation), type
                ) and issubclass(_t, Enum):
                    while True:
                        items = _choice_prompt(
                            f"請選擇{prefix}第 {len(items) + 1} 筆「{v.title or k.title()}」？",
                            _t,
                            lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",
                            default="",
                            is_required=False,
                            post_value_proc=lambda _: (
                                _model_field_proc(t, k, items + [_], **context)
                                if _
                                else items + [_]
                            ),
                        )
                        if "" == items[-1]:
                            result[k] = items[:-1]
                            break
                else:
                    while True:
                        if (v.json_schema_extra or {}).get("allow_multiple_lines"):  # type: ignore[union-attr]
                            click.termui.visible_prompt_func = _multiple_prompt
                        items = click.prompt(
                            f"請輸入{prefix}第 {len(items) + 1} 筆「{v.title or k.title()}」",
                            default="",
                            value_proc=lambda _: (
                                _model_field_proc(t, k, items + [_], **context)
                                if _
                                else items + [_]
                            ),
                            show_default=False,
                        )
                        click.termui.visible_prompt_func = input
                        if "" == items[-1]:
                            result[k] = items[:-1]
                            break
        elif isinstance(_t := next_not_none_type(v.annotation), type) and issubclass(
            _t, BaseModel
        ):
            result[k] = _model_prompt(
                _t,
                prefix=f"{prefix}「{v.title or k.title()}」的",
                callable=lambda **_: _model_field_proc(t, k, _, **context),
                **context,
            )
        elif isinstance(_t := next_not_none_type(v.annotation), type) and issubclass(
            _t, Enum
        ):
            result[k] = _choice_prompt(
                f"請選擇{prefix}「{v.title or k.title()}」？",
                _t,
                lambda k, v: f"({k}) {getattr(v, "displayname", v.name)}",
                default=None if v.is_required() else v.get_default(),
                is_required=v.is_required(),
            )
        else:
            if (v.json_schema_extra or {}).get("allow_multiple_lines"):  # type: ignore[union-attr]
                click.termui.visible_prompt_func = _multiple_prompt
            result[k] = click.prompt(
                f"請輸入{prefix}「{v.title or k.title()}」",
                default=None if v.is_required() else "",
                value_proc=lambda _: _model_field_proc(t, k, _, **context),
                show_default=False,
            )
            click.termui.visible_prompt_func = input
    else:
        callable(**result)
        return result


def _multiple_prompt(prompt_text: object = ""):
    if "|" == (
        _ := input(
            prompt_text
            + add_comment(
                "本欄位支援多行字串編輯模式。進入請按【|】以開啟多行字串編輯模式。"
            )
        )
    ):
        inp = []
        click.echo(
            add_comment(
                "進入多行文字編輯模式。結束請於換行後連按兩次【Enter】以提交輸入。",
                "",
                "",
            )
        )
        last_is_empty = False
        while (__ := input("> ").strip()) or not last_is_empty:
            inp.append(__)
            last_is_empty = not bool(__)
        _ = "\n".join(inp) if any(inp) else ""
    return _


def _pattern_proc(pattern: str | re.Pattern, value: str):
    if re.match(pattern, value):
        return value
    else:
        raise click.UsageError(
            click.style(f"{truncate(value)!r} is not a valid format.", fg="red")
            + add_comment(
                f"String should match pattern {pattern!r} [input_value={value!r}]"
            )
        )

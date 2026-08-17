import itertools
import math
import os
import re
import shutil
import subprocess
import textwrap
import time
import types
import typing
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from functools import cache, wraps
from gettext import gettext as _
from pathlib import Path
from typing import Callable, Iterable, Literal, TypeVar, get_args, get_origin

import yaml
from wcwidth import wcswidth

T = TypeVar("T")


def apply_monkey_patches():
    """Apply runtime patches for terminal rendering.

    Fix width calculation with CJK/emoji and improve Click exception styling.
    """
    from click import _compat, exceptions, formatting, style

    def _patch_click_exception(self: exceptions.ClickException):
        self.message = style(  # type: ignore[misc]
            (parts := self.message.split("\n", 1))[0],
            fg="red",
        ) + (f"\n{parts[1]}" if len(parts) > 1 else "")

    exceptions.ClickException.__init__ = _patch_init(
        exceptions.ClickException.__init__, _patch_click_exception
    )

    @wraps(formatting.term_len)
    def _term_len(x: str):
        return wcswidth(_compat.strip_ansi(x))

    formatting.term_len = _term_len  # type: ignore[method-assign]


def clear_dir(path: Path):
    """Remove all files, subdirectories, and symlinks in the given directory.

    :param path: Target dictionary to clean.
    """
    if path.is_dir():
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file() or entry.is_symlink():
                    os.unlink(entry.path)
                elif entry.is_dir():
                    shutil.rmtree(entry.path)


def dump_yaml(
    data: dict,
    indent=0,
    offset=2,
    nest_level=0,
    section_break_keys: Iterable[str] = (),
    plain_scalar_keys: Iterable[str] = (),
    block_scalar_keys: Iterable[str] = (),
):
    """Serialize a Python dict to a YAML-like list of strings.

    - Handles nested dicts and lists.
    - Indents nested structures for readability.
    - Uses block style for long/multiline strings.
    - Supports custom formatting for specific fields.

    :param data: Input dictionary to serialize.
    :param indent: Current indentation level.
    :param offset: Indentation increment for nested structures and sequence items.
    :param nest_level: Recursion depth for formatting control.
    :param section_break_keys: Fields that trigger a blank line before their section for readability.
    :param plain_scalar_keys: Fields to always use plain style (no block/fold).
    :param block_scalar_keys: Fields to always use block style (| or >) for multi-line strings.
    :returns: List of YAML-formatted strings.
    """
    lines: list[str] = []
    spaces = " " * indent
    _not_en = re.compile(
        r"[^\u0000-\u007F’“”]"
    )  # Matches any character NOT ASCII or common English smart quotes

    def _scalar(v):
        """Serialize a value as a single-line YAML scalar.

        - `allow_unicode`: emit CJK characters as-is instead of ASCII escape sequences.
        - `width=math.inf`: disable wrapping so `splitlines` never truncates.

        .. note::
            Strings containing newlines must be routed to block style (`|`) by the caller beforehand.
        """
        return yaml.safe_dump(v, allow_unicode=True, width=math.inf).splitlines()[0]

    for k, v in data.items():
        if k in section_break_keys and not nest_level and lines and lines[-1]:
            lines.append("")  # blank line before footers

        if v is None:
            lines.append(f"{spaces}{k}:")
        elif isinstance(v, str):
            if k in plain_scalar_keys:
                lines.append(f"{spaces}{k}: {_scalar(v)}")
            elif "\n" in v or (
                k in block_scalar_keys and not nest_level and _not_en.search(v)
            ):
                lines.append(f"{spaces}{k}: |")
                lines.extend(
                    f"{spaces}{' ' * offset}{line}" if line else ""
                    for line in v.splitlines()
                )
                lines.append("")  # blank line after block
            elif 70 < len(v) or (k in block_scalar_keys and not nest_level):
                lines.append(f"{spaces}{k}: >")
                lines.extend(
                    f"{spaces}{' ' * offset}{line}" if line else ""
                    for line in textwrap.wrap(
                        v,
                        width=70,
                        tabsize=4,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
                lines.append("")  # blank line after block
            else:
                lines.append(f"{spaces}{k}: {_scalar(v)}")
        elif isinstance(v, list):
            if not v:
                lines.append(f"{spaces}{k}: []")
            elif any(not isinstance(item, dict) for item in v):
                lines.append(f"{spaces}{k}:")
                lines.extend(f"{spaces}{' ' * offset}- {_scalar(item)}" for item in v)
            else:
                lines.append(f"{spaces}{k}:")
                for item in v:
                    if sublines := dump_yaml(
                        item,
                        indent + offset + 2,
                        offset,
                        nest_level + 1,
                        section_break_keys,
                        plain_scalar_keys,
                        block_scalar_keys,
                    ):
                        # Add dash to the first line, indent the rest
                        lines.append(f"{spaces}{' ' * offset}- {sublines[0].lstrip()}")
                        lines.extend(sublines[1:])
        elif isinstance(v, dict):
            lines.append(f"{spaces}{k}:")
            lines.extend(
                dump_yaml(
                    v,
                    indent + offset,
                    offset,
                    nest_level + 1,
                    section_break_keys,
                    plain_scalar_keys,
                    block_scalar_keys,
                )
            )
        else:
            lines.append(f"{spaces}{k}: {_scalar(v)}")

    return lines


def fit(
    s,
    width=12,
    placeholder="...",
    fillchar=" ",
    align: Literal["left", "center", "right"] = "left",
):
    """Resize text to fit the given display width (handles wide characters).

    Pads with fillchar if the text is shorter than the given width.
    Truncates and appends placeholder if the text exceeds the given width.
    Supports left, right, and center alignment.

    Use empty strings ("") for placeholder or fillchar to disable truncation
    indicator or padding when not needed.

    If the input is not a string, it will be auto-converted using :py:meth:`str`.
    Properly handles Unicode wide characters (CJK, emojis) and skips control characters.

    .. note::
        - Control characters (ASCII 0-31, 127) are skipped during truncation as they
          typically have no visual representation in terminal output.
        - Input text should be pre-sanitized to remove ANSI escape sequences
          (color codes, cursor movement, etc.) as these are not handled by this function.
        - Very complex Unicode sequences (some emoji combinations) may not be
          handled perfectly in all edge cases.

    Examples
    ---
    .. code-block:: python
        import string

        # Left alignment - truncate from end
        assert fit(string.ascii_uppercase, align="left") == "ABCDEFGHI..."

        # Right alignment - truncate from start
        assert fit(string.ascii_uppercase, align="right") == "...RSTUVWXYZ"

        # Center alignment - truncate from both ends
        assert fit(string.ascii_uppercase, align="center") == "ABCD...VWXYZ"

        # Wide characters (CJK & Emoji)
        s = "👋(你好/こんちゃ/안녕)"
        assert wcswidth(s) > len(s)
        assert fit(s, width=24, fillchar="-", align="center") == f"-{s}-"

        # Disable placeholder and skip control characters
        s = "Hello World"
        assert fit(f"{chr(0)}".join(s), placeholder="") == s

        # Original input not string type
        assert fit(list(range(100)), 8, placeholder=" ~ ", align="center") == "[0 ~ 99]"

    :param s: Original content.
    :param width: Maximum display width in terminal columns. Must be at least 1.
    :param placeholder: Text inserted when truncation occurs (default: ellipsis).
    :param fillchar: Character used for padding when text is shorter than width.
    :param align: Text alignment within the specified width.
    :returns: Text fitted to the exact specified display width.
    :raises ValueError: If parameters are invalid.
    """
    if not isinstance(s, str):
        s = str(s)
    if 0 >= width:
        raise ValueError(f"Invalid alignment value, get {width=}")
    elif not placeholder.isprintable():
        raise ValueError(f"Invalid alignment value, get {placeholder=}")
    elif 1 < len(fillchar) or not fillchar.isprintable():
        raise ValueError(f"Invalid alignment value, get {fillchar=}")
    elif (original_width := max(wcswidth(s), len(s))) <= width:
        match align:
            case "left":
                return s + fillchar * (width - original_width)
            case "right":
                return fillchar * (width - original_width) + s
            case "center":
                left_pad = (width - original_width) // 2
                right_pad = width - original_width - left_pad
                return fillchar * left_pad + s + fillchar * right_pad
            case _:
                raise ValueError(f"Invalid alignment value, get {align=}")
    elif 0 >= (available_width := width - wcswidth(placeholder)):
        return placeholder
    else:
        current_width, result = 0, ""
        match align:
            case "left":
                for char in s:
                    if 0 >= (char_width := wcswidth(char)):
                        # If this char has no printable effect on a terminal, e.g., '\0', skip
                        continue
                    elif available_width < current_width + char_width:
                        # If adding this char would exceed, break
                        break
                    else:
                        result += char
                        current_width += char_width
                return result + placeholder
            case "right":
                for char in reversed(s):
                    if 0 >= (char_width := wcswidth(char)):
                        # If this char has no printable effect on a terminal, e.g., '\0', skip
                        continue
                    elif available_width < current_width + char_width:
                        # If adding this char would exceed, break
                        break
                    else:
                        result = char + result
                        current_width += char_width
                return placeholder + result
            case "center":
                return str(
                    fit(s, start_width := (available_width // 2), "", fillchar)
                    + placeholder
                    + fit(s, available_width - start_width, "", fillchar, "right")
                )
            case _:
                raise ValueError(f"Invalid alignment value, get {align=}")


def get_display_path(path: Path | str):
    """Get cross-platform relative path for display.

    Paths inside the current working directory become relative to it,
    keeping full system paths out of logs; others stay absolute.
    Purely lexical (no filesystem access), POSIX-style separators.

    Examples
    ---
    .. code-block:: python
        assert get_display_path("") == "."
        assert get_display_path(Path.cwd() / "out/bundle.json") == "out/bundle.json"

    :param path: Absolute or relative path to convert.
    :returns: Display path string with forward slashes.
    """
    absolute = Path(os.path.abspath(path))
    return (
        absolute.relative_to(cwd)
        if absolute.is_relative_to(cwd := Path.cwd())
        else absolute
    ).as_posix()


def get_git_metadata(files: list[Path]):
    """Query git history for file metadata.

    Uses a single subprocess to query all files efficiently.
    Falls back gracefully if git is unavailable.

    .. seealso::
        `git-log documentation <https://git-scm.com/docs/git-log>`_

    :param files: List of file paths to query.
    :returns: Mapping POSIX filepaths to metadata dict (created, modified, etc.).
    """
    metadata: defaultdict[str, dict] = defaultdict(dict)
    try:
        if files:
            cwd = Path.cwd().resolve()
            for chunk in subprocess.run(
                ["git", "--no-pager", "log", "--format=%n%n%aI", "--name-only", "--"]
                + (
                    list(paths)
                    if 0
                    < len(
                        paths := {
                            path.parts[0]
                            for file in files
                            if (
                                path := (
                                    resolved.relative_to(cwd)
                                    if (resolved := file.resolve()).is_relative_to(cwd)
                                    else None
                                )
                            )
                            and path.parts
                            and path.parts[0] not in (os.curdir, os.pardir)
                        }
                    )
                    < 50
                    else []
                ),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.split("\n\n\n"):
                lines = iter(chunk.splitlines())
                if first := next(lines, None):
                    committed = datetime.fromisoformat(first)
                    for line in lines:
                        if line:
                            if line not in metadata:
                                metadata[line]["modified"] = committed
                            metadata[line]["created"] = committed
    except Exception:
        pass
    return metadata


def get_unique_path(path: Path, max_attempt=100):
    """Return a unique file or directory path by appending a number if needed.

    Ensures the parent directory exists. If the given path already exists,
    appends ' (1)', ' (2)', etc. before the extension until a non-existing path is found,
    up to `max_attempt` tries.

    :param path: The initial file or directory path to check.
    :param max_attempt: Maximum number of attempts to find a unique path.
    :returns: A unique Path object that does not exist on disk.
    :raises FileExistsError: If a unique path cannot be found within `max_attempt` tries.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stem, suffix = path.stem, path.suffix
        for i in itertools.count(1):
            candidate_path = path.parent / f"{stem} ({i}){suffix}"
            if not candidate_path.exists():
                return candidate_path
            elif max_attempt <= i:
                raise FileExistsError(
                    _("Too many attempts to create {path!r}.").format(
                        path=path.as_posix()
                    )
                )

    return path


def load_files(
    paths: Path | Iterable[Path],
    *extensions: str,
    encoding: str | None = None,
    recursive=False,
    ignore_hidden=True,
):
    """Load files with specific extensions from given paths, filtering by criteria.

    Supports both simple (e.g., '.py') and compound (e.g., '.min.js', '.tar.gz') extensions.

    If no extensions are given, all files are returned.

    :param paths: One or more paths (files and directories) to search.
    :param extensions: File extensions to filter by (case-insensitive).
    :param encoding: If given, validate the file encoding (e.g., 'utf-8').
    :param recursive: Search subdirectories recursively or not.
    :param ignore_hidden: Ignore hidden files (those starting with a dot) or not.
    :returns: List of matching file paths.
    """
    extensions = tuple(set({extension.lower() for extension in extensions}))
    filepaths: set[Path] = set()
    for path in (paths,) if isinstance(paths, Path) else paths:
        if path.is_dir():
            method = path.rglob if recursive else path.glob
            if not extensions:
                filepaths.update(method("*"))
            else:
                for extension in extensions:
                    filepaths.update(method(f"*{extension}"))
        else:
            filepaths.add(path)

    def _filter(filepath: Path):
        if not filepath.is_file():
            return False
        elif ignore_hidden and filepath.name.startswith("."):
            # Filename preceded by dot should be hidden
            return False
        elif encoding:
            try:
                # Try reading to verify it's valid encoding
                filepath.read_text(encoding=encoding)
            except UnicodeDecodeError:
                return False
        elif extensions and not any(
            filepath.name.endswith(extension) for extension in extensions
        ):
            return False
        else:
            return True

    return list(filter(_filter, filepaths))


def next_non_none_type(tp):
    """Get the first non-`None` type argument in substitutions performed.

    Examples
    ---
    .. code-block:: python
        assert next_non_none_type(Dict[str, int]) is dict
        assert next_non_none_type(str) is str
        assert next_non_none_type(List) is list
        assert next_non_none_type(List[T | None][Dict[str, int]]) is dict
        assert next_non_none_type(Union[None, Union[T, float], str][int]) is int
        assert next_non_none_type(Optional[Tuple[T, int]][str]) is str

    :param tp: Unknown input.
    :returns: Original input if not found, else the first type.
    """

    def _next():
        return next(
            (arg for arg in get_args(tp) if arg and arg is not types.NoneType),
            None,
        )

    match (origin_type := get_origin(tp)):
        case typing.Union | types.UnionType | typing.Annotated:
            return next_non_none_type(_next())
        case _:
            if not isinstance(result := origin_type or tp, type):
                return type(result)
            elif issubclass(result, (list, set, tuple)) and (
                origin_type := next_non_none_type(_next())
            ) not in (None, types.NoneType):
                return origin_type
            return result


def none_on_error(func: Callable[..., T]) -> Callable[..., T | None]:
    """Wrap a function and return `None` on error.

    :param func: Function to wrap.
    :returns: Wrapped function that returns `None` when an exception occurs.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    return wrapper


def sanitize_path(*parts: str, max_length=1000, max_segment_length=100):
    """Remove dangerous path components entirely.

    :param parts: Path segments to sanitize.
    :param max_length: Maximum allowed total path length.
    :param max_segment_length: Maximum allowed segment length.
    :returns: Sanitized path with dangerous components removed.
    :raises ValueError: For invalid input or security violations
    """
    if not parts:
        return ""

    segments = []

    # Process each part
    for part in parts:
        if not (part := part.strip()):
            # Skip empty parts
            continue
        elif any(char in part for char in "\\\x00\r\n\t"):
            # reject dangerous characters
            raise ValueError("Dangerous characters")
        else:
            # Split each part by slash and process segments
            for segment in part.split("/"):
                if not (segment := segment.strip(". ")):
                    # Skip empty segments and those with only dots/spaces
                    continue
                elif (_ := len(segment)) > max_segment_length:
                    # Validate segment length
                    raise ValueError(
                        f"Segment too long ({_} > {max_segment_length}): {segment!r}"
                    )
                else:
                    # Only add non-empty segments
                    segments.append(segment)
    else:
        # Join all segments
        if (_ := len(result := "/".join(segments))) > max_length:
            # Validate total length
            raise ValueError(f"Path too long ({_} > {max_length})")

    return result


@contextmanager
def timeit(logger: Callable[[str], None] = print):
    """Measure elapsed time of a code block.

    :param logger: Callback to receive the formatted duration.
    """
    start_time = time.monotonic()
    try:
        yield
    finally:
        logger(
            _("Elapsed: {duration:,.2f} sec").format(
                duration=time.monotonic() - start_time
            )
        )


@cache
def to_kebab_case(s: str):
    """Convert text to kebab case.

    Separates words with a dash character (-) in lowercase.

    :param s: Input string.
    :returns: Text formatted using kebab case.
    """
    return re.sub(r"(?:[ _.]|([a-z0-9])([A-Z]))", r"\1-\2", s).lower()


@cache
def to_snake_case(s: str):
    """Convert text to snake case.

    Separates words with an underscore character (_) in lowercase.

    :param s: Input string.
    :returns: Text formatted using snake case.
    """
    return re.sub(r"(?:[ .-]|([a-z0-9])([A-Z]))", r"\1_\2", s).lower()


def _patch_init(original_init, *funcs: Callable[[T], None], **default_kwargs):
    """Create a secure monkey patch for `__init__` methods.

    :param original_init: The original `__init__` method to patch.
    :param funcs: Functions that take self and modify it after original `__init__`.
    :param default_kwargs: Default parameter values to override in the original `__init__`.
    :returns: A new `__init__` method that calls original with merged parameters then applies modifications.
    """

    @wraps(original_init)
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **(default_kwargs | kwargs))
        for fn in funcs:
            fn(self)

    return patched_init

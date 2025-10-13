import subprocess
import types
import typing
from importlib.metadata import version
from pathlib import Path
from typing import Iterable, get_args, get_origin

try:
    VERSION = version(__package__.split(".")[0])
except Exception:
    try:
        VERSION = subprocess.check_output(
            ["git", "describe", "--tags"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        VERSION = "0.0.0+dev"


def load_files(paths: Iterable[Path], extensions: Iterable[str], recursive=False):
    """Load files with specified extensions from the target files or directories.

    This function searches the specified paths for files with the given extensions.
    If a directory is provided, it can search recursively through its subdirectories based on the `recursive` flag.

    :param strPaths: Target files or directories to search
    :param extensions: File extensions to filter by (e.g., '.json', '.yml').
    :param recursive: Search recursively in subdirectories or not
    :return: Legal file paths match the specified extensions
    """
    filepaths: list[Path] = []
    for path in paths:
        if path.is_dir():
            method = path.rglob if recursive else path.glob
            for extension in extensions:
                filepaths.extend(method(f"*{extension}"))
        elif path.is_file() and path.suffix.lower() in extensions:
            filepaths.append(path)
    return filepaths


def nget(n: int | float, unit1: str, unit2: str | None = None, *, nformat=""):
    """Returns a string representing the number and unit.

    Additional functions for plural forms.

    Most singular nouns form the plural by adding -s.

    Examples::

        >>> assert nget(1, "person", "people") == "1 person"
        >>> assert nget(23396049, "person", "people", nformat="+16,") == "     +23,396,049 people"
        >>> assert nget(250.375, "g", nformat=".2f") == "250.38 g"

    :param n: Number
    :param unit1: Singular form
    :param unit2: Plural form
    :param nformat: Number format
    :return: Formatted string
    """
    return f"{n:{nformat}} {unit1 if 1 == n else (unit2 or unit1 + 's')}"


def next_not_none_type(t):
    """Get first not `None` type argument in all substitutions performed.

    Examples::

        >>> assert next_not_none_type(Dict[str, int]) == dict
        >>> assert next_not_none_type(str) == str
        >>> assert next_not_none_type(List) == list
        >>> assert next_not_none_type(List[T | None][Dict[str, int]]) == dict
        >>> assert next_not_none_type(Union[None, Union[T, float], str][int]) == int
        >>> assert next_not_none_type(Optional[Tuple[T, int]][str]) == str

    :param t: Unknown input
    :return: Original input if not found else return first type
    """
    match (__ := get_origin(t)):
        case typing.Union | types.UnionType | typing.Annotated:
            return next_not_none_type(
                (
                    tuple(_ for _ in get_args(t) if _ and _ is not types.NoneType)
                    + (None,)
                )[0]
            )
        case _:
            result = __ or t
            if not isinstance(result, type):
                return type(result)
            elif result in (list, set, tuple) and (
                __ := next_not_none_type(
                    (
                        tuple(_ for _ in get_args(t) if _ and _ is not types.NoneType)
                        + (None,)
                    )[0]
                )
            ) not in (None, types.NoneType):
                return __
            return result


def truncate(s, max_length=50):
    """Truncate a string and insert '...' in the middle if too long.

    Examples::

        >>> assert truncate(" ".join("bla" for _ in range(10)), 12) == "bla ... bla"

    :param s: Original content
    :param max_length: Maximum length to display
    :return: Formatted text with ellipsis in the middle
    """
    if not isinstance(s, str):
        s = str(s)  # Auto-converted if input not string
    if len(s) <= max_length:
        return s
    half = (max_length - 3) // 2  # Subtract 3 for "..."
    return s[:half] + "..." + s[-half:]

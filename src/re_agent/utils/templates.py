"""Simple string-template rendering utilities."""

from __future__ import annotations

import string
from pathlib import Path


def render_template(template_path: Path, **variables: str) -> str:
    """Read a template file and substitute ``$variable`` placeholders.

    Uses :class:`string.Template.safe_substitute` so that unresolved
    placeholders are left as-is rather than raising an error.

    Args:
        template_path: Path to the template file.
        **variables: Key/value pairs to substitute.

    Returns:
        The rendered template string.

    Raises:
        FileNotFoundError: If the template file does not exist, with a message
            naming the path and the likely cause (broken/incomplete install).
        OSError: If the template file exists but cannot be read.
    """
    try:
        text = template_path.read_text(encoding="utf-8")
    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"Template file not found: {template_path}. The prompt templates ship with the package; "
            "a missing file usually means a broken or incomplete install."
        ) from err
    except OSError as err:
        raise OSError(f"Could not read template file {template_path}: {err}") from err
    tmpl = string.Template(text)
    return tmpl.safe_substitute(variables)


def render_template_string(template_text: str, **variables: str) -> str:
    """Substitute ``$variable`` placeholders in a template string.

    Uses :class:`string.Template.safe_substitute` so that unresolved
    placeholders are left as-is rather than raising an error.

    Args:
        template_text: The template string.
        **variables: Key/value pairs to substitute.

    Returns:
        The rendered string.
    """
    tmpl = string.Template(template_text)
    return tmpl.safe_substitute(variables)

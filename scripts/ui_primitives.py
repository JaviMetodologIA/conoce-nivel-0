"""Small governed UI primitives shared by legacy and module renderers."""

from __future__ import annotations


_ICON_PATHS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"></path>',
    "back": '<path d="M19 12H5m6 6-6-6 6-6"></path>',
    "external": (
        '<path d="M14 5h5v5M19 5l-8 8"></path>'
        '<path d="M17 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h5"></path>'
    ),
    "download": '<path d="M12 4v11m-4-4 4 4 4-4M5 20h14"></path>',
    "print": (
        '<path d="M7 9V4h10v5M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2"></path>'
        '<path d="M7 14h10v6H7z"></path>'
    ),
}


def ui_icon(name: str) -> str:
    """Return one local, decorative SVG icon from the closed icon set."""

    try:
        paths = _ICON_PATHS[name]
    except KeyError as error:
        raise ValueError(f"unknown UI icon: {name}") from error
    return f'<svg class="ui-icon" aria-hidden="true" viewBox="0 0 24 24">{paths}</svg>'


__all__ = ["ui_icon"]

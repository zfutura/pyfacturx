import gettext
from collections.abc import Callable
from pathlib import Path

LOCALE_PATH = Path(__file__).parent / "locale"


def setup_locale() -> Callable[[str], str]:
    """Setup the gettext translation function in a module.

    Usage:

    from ._locale import setup_locale
    _ = setup_locale()

    print(_("Hello, World!"))
    """

    t = gettext.translation("pyfactur-x", localedir=LOCALE_PATH, fallback=True)
    return t.gettext

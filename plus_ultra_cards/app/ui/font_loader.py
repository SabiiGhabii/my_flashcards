from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

def load_win95_font(app: Optional[QApplication] = None, base_point_size: int = 9) -> Optional[str]:
    """Load bundled Win95 font and set substitutions.

    Parameters
    ----------
    app: QApplication, optional
        If provided, the application's default font will be set.
    base_point_size: int
        Point size used when setting the application font.

    Returns
    -------
    str | None
        Name of the loaded (or fallback) font family.
    """
    font_file = "W95font.otf"
    search_paths = [
        Path(__file__).resolve().parents[1] / "assets" / "fonts" / font_file,
        Path(__file__).resolve().parents[2] / "assets" / "fonts" / font_file,
        Path.cwd() / "assets" / "fonts" / font_file,
        Path.cwd() / font_file,
        Path(__file__).resolve().parents[2] / font_file,
    ]

    loaded_family = None
    for path in search_paths:
        if path.exists():
            fid = QFontDatabase.addApplicationFont(str(path))
            if fid != -1:
                families = QFontDatabase.applicationFontFamilies(fid)
                if families:
                    loaded_family = families[0]
                    break

    if loaded_family:
        if app is not None:
            app.setFont(QFont(loaded_family, base_point_size))
        QFont.insertSubstitution("MS Sans Serif", loaded_family)
        QFont.insertSubstitution("Microsoft Sans Serif", loaded_family)
        QFont.insertSubstitution("Fixedsys", "Courier New")
        return loaded_family

    logger.warning("W95font.otf not found; using system fallback fonts.")
    fallback_family = None
    for family in ("Microsoft Sans Serif", "Tahoma", "Arial"):
        if family in QFontDatabase().families():
            fallback_family = family
            if app is not None:
                app.setFont(QFont(family, base_point_size))
            break

    if fallback_family:
        QFont.insertSubstitution("MS Sans Serif", fallback_family)
        QFont.insertSubstitution("Microsoft Sans Serif", fallback_family)
    else:
        fallback_family = "Arial"
        if app is not None:
            app.setFont(QFont(fallback_family, base_point_size))
        QFont.insertSubstitution("MS Sans Serif", fallback_family)
        QFont.insertSubstitution("Microsoft Sans Serif", fallback_family)

    QFont.insertSubstitution("Fixedsys", "Courier New")
    return fallback_family

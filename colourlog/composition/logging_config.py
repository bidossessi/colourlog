# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

LOG_FORMAT: Final = "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)s: %(message)s"
DATE_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
ENV_LEVEL: Final = "COLOURLOG_LOG_LEVEL"
ENV_FILE: Final = "COLOURLOG_LOG_FILE"
UVICORN_LOGGERS: Final = ("uvicorn", "uvicorn.error", "uvicorn.access")
ROTATE_MAX_BYTES: Final = 10 * 1024 * 1024
ROTATE_BACKUP_COUNT: Final = 5


def configure_logging(
    level: str | int | None = None,
    log_file: Path | str | None = None,
) -> None:
    resolved_level = level if level is not None else os.environ.get(ENV_LEVEL, "INFO").upper()
    resolved_file = log_file if log_file is not None else os.environ.get(ENV_FILE)

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    handlers: list[logging.Handler] = []

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    handlers.append(stream)

    if resolved_file:
        path = Path(resolved_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        file_h = RotatingFileHandler(
            path,
            maxBytes=ROTATE_MAX_BYTES,
            backupCount=ROTATE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_h.setFormatter(formatter)
        handlers.append(file_h)

    root = logging.getLogger()
    root.handlers.clear()
    for h in handlers:
        root.addHandler(h)
    root.setLevel(resolved_level)

    for name in UVICORN_LOGGERS:
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True

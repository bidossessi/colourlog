# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
from pathlib import Path

import uvicorn

from colourlog.composition.container import build_sqlite_container
from colourlog.composition.fastapi_app import create_app
from colourlog.composition.logging_config import ENV_FILE, configure_logging

DEFAULT_DB_PATH = Path.home() / ".local/share/colourlog/db.sqlite"
DEFAULT_LOG_PATH = Path.home() / ".local/state/colourlog/colourlog.log"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18765

logger = logging.getLogger(__name__)


def main() -> None:
    log_path = Path(os.environ.get(ENV_FILE) or DEFAULT_LOG_PATH).expanduser()
    configure_logging(log_file=log_path)
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "starting colourlog daemon db=%s host=%s port=%d log=%s",
        DEFAULT_DB_PATH,
        DEFAULT_HOST,
        DEFAULT_PORT,
        log_path,
    )
    container = build_sqlite_container(DEFAULT_DB_PATH)
    app = create_app(container)
    uvicorn.run(
        app,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        log_config=None,
    )


if __name__ == "__main__":
    main()

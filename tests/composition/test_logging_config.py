# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest
from colourlog.composition.logging_config import ENV_FILE, ENV_LEVEL, configure_logging


@pytest.fixture(autouse=True)
def _reset_root_after_test():
    yield
    logging.getLogger().handlers.clear()
    logging.getLogger().setLevel(logging.WARNING)


def test_default_level_info_with_stdout_handler():
    configure_logging()
    root = logging.getLogger()
    assert root.level == logging.INFO
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0], logging.StreamHandler)


def test_explicit_level_argument_wins():
    configure_logging(level="DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_env_var_level_picked_up(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(ENV_LEVEL, "WARNING")
    configure_logging()
    assert logging.getLogger().level == logging.WARNING


def test_log_file_arg_adds_rotating_handler(tmp_path: Path):
    log_path = tmp_path / "subdir" / "colourlog.log"
    configure_logging(log_file=log_path)
    handlers = logging.getLogger().handlers
    assert len(handlers) == 2
    file_handlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert Path(file_handlers[0].baseFilename) == log_path
    assert log_path.parent.exists()


def test_log_file_env_var_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    log_path = tmp_path / "via-env.log"
    monkeypatch.setenv(ENV_FILE, str(log_path))
    configure_logging()
    handlers = logging.getLogger().handlers
    file_handlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert Path(file_handlers[0].baseFilename) == log_path


def test_log_emitted_to_file(tmp_path: Path):
    log_path = tmp_path / "out.log"
    configure_logging(level="INFO", log_file=log_path)
    logging.getLogger("colourlog.test").info("hello %s", "world")
    for h in logging.getLogger().handlers:
        h.flush()
    content = log_path.read_text(encoding="utf-8")
    assert "hello world" in content
    assert "colourlog.test" in content
    assert "INFO" in content


def test_uvicorn_loggers_propagate(tmp_path: Path):
    configure_logging()
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        assert lg.handlers == []
        assert lg.propagate is True

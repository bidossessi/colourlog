# colourlog

[![CI](https://github.com/bidossessi/colourlog/actions/workflows/ci.yml/badge.svg)](https://github.com/bidossessi/colourlog/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/bidossessi/colourlog/branch/main/graph/badge.svg)](https://codecov.io/gh/bidossessi/colourlog)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-blue.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Conventional Commits](https://img.shields.io/badge/conventional%20commits-1.0.0-yellow.svg)](https://www.conventionalcommits.org/)

Personal, self-hosted, GNOME-native time tracker. Consumes ActivityWatch buckets, supports manual + auto task switching via keywords + calendar, exports `detailed.csv` for the monthly timesheet pipeline.

Status: pre-alpha. Phase 0 (AW headless) + Phase 1 (daemon skeleton + CRUD) + Phase 2 ledger foundations done.

## Requirements

- Ubuntu 24.04 (X11 today; Wayland deferred)
- GNOME Shell 46
- Python 3.12+
- ActivityWatch installed (upstream `.deb` — see `var/plan.md` Phase 0)

## Setup

**System prerequisites** (Ubuntu 24.04 noble):

```sh
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
                 libgirepository1.0-dev libcairo2-dev pkg-config
```

These provide GTK3 + AppIndicator + the headers PyGObject builds against.

**Project setup**:

```sh
make venv       # create .venv (python3.12)
make install    # pip install -e .[dev,gtk] + install pre-commit git hooks
make check      # run all gates: lint + types + tests + import contract
```

**Running**:

```sh
make run        # daemon: uvicorn on 127.0.0.1:18765
make tray       # tray indicator (requires GUI session)
```

`make install` also wires the git hooks (`.git/hooks/pre-commit` + `commit-msg`). After that, every `git commit` auto-runs ruff + mypy + lint-imports + commitizen (conventional-commit format check on the message).

## Daily commands

| | |
|---|---|
| `make check` | full gate sweep |
| `make fix` | ruff auto-fix + format |
| `make test` | pytest + coverage only |
| `make run` | launch daemon (uvicorn on 127.0.0.1:18765, log → `var/log/colourlog.log`) |
| `make tray` | launch GTK3 tray (needs daemon running) |

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/) via [commitizen](https://commitizen-tools.github.io/commitizen/). Enforced on commit-msg by the pre-commit framework.

- `feat: ...` — new feature
- `fix: ...` — bug fix
- `chore: ...` — tooling / non-code housekeeping
- `docs: ...` — docs only
- `refactor: ...` — code change without behavior change
- `test: ...` — tests only

Interactive prompt: `.venv/bin/cz commit`. Bump version + regenerate changelog: `.venv/bin/cz bump --changelog`.

## License

GPL-3.0-or-later. See `LICENSE`.

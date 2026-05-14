# colourlog

Personal, self-hosted, GNOME-native time tracker. Consumes ActivityWatch buckets, supports manual + auto task switching via keywords + calendar, exports `detailed.csv` for the monthly timesheet pipeline.

Status: pre-alpha. Phase 0 (AW headless) + Phase 1 (daemon skeleton + CRUD) + Phase 2 ledger foundations done.

## Requirements

- Ubuntu 24.04 (X11 today; Wayland deferred)
- GNOME Shell 46
- Python 3.12+
- ActivityWatch installed (upstream `.deb` — see `var/plan.md` Phase 0)

## Setup

```sh
make venv       # create .venv (python3.12)
make install    # pip install -e .[dev] + install pre-commit git hooks
make check      # run all gates: lint + types + tests + import contract
```

`make install` also wires the git hooks (`.git/hooks/pre-commit` + `commit-msg`). After that, every `git commit` auto-runs ruff + mypy + lint-imports + commitizen (conventional-commit format check on the message).

## Daily commands

| | |
|---|---|
| `make check` | full gate sweep |
| `make fix` | ruff auto-fix + format |
| `make test` | pytest + coverage only |
| `make run` | launch daemon (uvicorn on 127.0.0.1:18765, log → `var/log/colourlog.log`) |

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

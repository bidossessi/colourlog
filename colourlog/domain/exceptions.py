# SPDX-License-Identifier: GPL-3.0-or-later


class DomainError(Exception):
    pass


class InvalidNameError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(f"name must be non-empty after stripping; got {value!r}")
        self.value = value


class InvalidKeywordError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(f"keyword must be lowercase, stripped, non-empty; got {value!r}")
        self.value = value


class NaiveDatetimeError(DomainError):
    def __init__(self, field: str, value: object) -> None:
        super().__init__(f"{field} must be timezone-aware; got {value!r}")
        self.field = field
        self.value = value


class EndBeforeStartError(DomainError):
    def __init__(self, start: object, end: object) -> None:
        super().__init__(f"end must be >= start; got start={start!r}, end={end!r}")
        self.start = start
        self.end = end


class SourceMatchSourceMismatchError(DomainError):
    def __init__(self, source: object, match_source: object) -> None:
        super().__init__(
            f"source/match_source mismatch: source={source!r}, match_source={match_source!r}"
        )
        self.source = source
        self.match_source = match_source


class InvalidTextFieldError(DomainError):
    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"{field} must be stripped non-empty when present; got {value!r}")
        self.field = field
        self.value = value


class IncoherentStopEventError(DomainError):
    def __init__(self, task_id: object, source: object) -> None:
        super().__init__(
            "task_id and source must both be set (start event) or both be None "
            f"(stop event); got task_id={task_id!r}, source={source!r}"
        )
        self.task_id = task_id
        self.source = source


class SubtaskWithoutTaskError(DomainError):
    def __init__(self, subtask_id: object) -> None:
        super().__init__(f"subtask_id requires task_id to be set; got subtask_id={subtask_id!r}")
        self.subtask_id = subtask_id

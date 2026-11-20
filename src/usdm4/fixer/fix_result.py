import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Change:
    """One change made to the JSON, for the audit log."""

    step: str
    path: str
    klass: str
    attribute: str
    old: Any
    new: Any
    reason: str


@dataclass
class Issue:
    """Something a step found and deliberately did not change."""

    step: str
    path: str
    klass: str
    attribute: str
    value: Any
    message: str


@dataclass
class FixResult:
    data: dict
    changes: list[Change] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    def change(self, step, path, klass, attribute, old, new, reason) -> None:
        self.changes.append(Change(step, path, klass, attribute, old, new, reason))

    def issue(self, step, path, klass, attribute, value, message) -> None:
        self.issues.append(Issue(step, path, klass, attribute, value, message))

    def summary(self) -> dict:
        counts = {"changes": {}, "issues": {}}
        for c in self.changes:
            counts["changes"][c.step] = counts["changes"].get(c.step, 0) + 1
        for i in self.issues:
            counts["issues"][i.step] = counts["issues"].get(i.step, 0) + 1
        return counts

    def to_log(self) -> dict:
        return {
            "summary": self.summary(),
            "changes": [asdict(c) for c in self.changes],
            "issues": [asdict(i) for i in self.issues],
        }

    def save(self, file_path: str, indent: int | None = 2) -> None:
        with open(file_path, "w") as f:
            json.dump(self.data, f, indent=indent, ensure_ascii=False)

    def save_log(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            json.dump(self.to_log(), f, indent=2, ensure_ascii=False)

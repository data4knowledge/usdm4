# MANUAL: do not regenerate
#
# Global id uniqueness within the study version. CORE-001015 walks
# `**.*[id and instanceType]`, groups by id and reports groups with count
# > 1. DataStore._ids dedupes by overwriting (so iterating it misses
# duplicates) — so we walk the raw JSON tree directly, tracking a
# JSONPath for each occurrence so multiple paths can be reported for a
# repeated id.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00083(RuleTemplate):
    """
    DDF00083: Within a study version, all id values must be unique.

    Applies to: All
    Attributes: id
    """

    def __init__(self):
        super().__init__(
            "DDF00083",
            RuleTemplate.ERROR,
            "Within a study version, all id values must be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        root = getattr(data, "data", None)
        if root is None:
            return self._result()

        occurrences: dict = defaultdict(list)
        _collect(root, "$", occurrences)

        for iid, hits in occurrences.items():
            if len(hits) <= 1:
                continue
            for itype, path in hits:
                self._add_failure(
                    f"id {iid!r} is not unique ({len(hits)} occurrences)",
                    itype or "Unknown",
                    "id",
                    path,
                )
        return self._result()


def _collect(node, path: str, occurrences: dict) -> None:
    """Recursive walk collecting (id -> [(instanceType, path), ...]).

    An 'instance' is a dict that carries both `id` and `instanceType`,
    mirroring CORE-001015's `**.*[id and instanceType]` filter.
    """
    if isinstance(node, dict):
        iid = node.get("id")
        itype = node.get("instanceType")
        if isinstance(iid, str) and isinstance(itype, str):
            occurrences[iid].append((itype, path))
        for key, child in node.items():
            _collect(child, f"{path}.{key}", occurrences)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _collect(child, f"{path}[{index}]", occurrences)

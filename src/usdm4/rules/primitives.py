"""
Primitives used by generated rule bodies.

These helpers sit on top of usdm4.data_store.DataStore and encapsulate the
small number of operations that recur across rule implementations. Keeping
them here (rather than inlining into every generated rule) makes the
generated code short, readable, and easy to audit.

Design principle: DataStore provides the index primitives
(instances_by_klass, instance_by_id, parent_by_klass, path_by_id). This
module adds *composite* helpers that sit one level up — things like
"find duplicates by key", "resolve an id list via DataStore", etc.

Intentionally small. If a helper is only used by one rule it lives in
that rule's body, not here.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Optional


def children(instance: dict, attr: str) -> list:
    """
    Safe iteration of an instance's child-list attribute.

    Equivalent to JSONata `$p.<attr>` where the attribute may be None,
    missing, or empty.
    """
    return instance.get(attr) or []


def duplicates_by(items: Iterable[dict], key_fn: Callable[[dict], Any]) -> list[dict]:
    """
    Return items whose `key_fn(item)` value occurs more than once.

    JSONata equivalent:
        $filter($a, function($v,$i,$a){$count($a[key=$v.key])>1})
    """
    buckets: dict[Any, list[dict]] = defaultdict(list)
    for it in items:
        k = key_fn(it)
        if k is None or k == "":
            continue
        buckets[k].append(it)
    return [it for group in buckets.values() if len(group) > 1 for it in group]


def duplicate_values(values: Iterable) -> list:
    """
    Return values that appear more than once in the input list.

    JSONata equivalent for intra-attribute duplicates:
        $filter($arr, function($v,$i,$a){$count($a[$=$v])>1})
    """
    counts: dict[Any, int] = defaultdict(int)
    for v in values or []:
        counts[v] += 1
    return [v for v, n in counts.items() if n > 1]


def not_in_set(target: Any, allowed: Iterable) -> bool:
    """
    True when target is not present in allowed.

    JSONata equivalent: `$not($target in $allowed)`.
    """
    return target not in (allowed or [])


def any_ids_unresolved(ids: Iterable[str], data_store) -> list[str]:
    """
    Given a list of id references, return those that do not resolve to an
    instance via DataStore.instance_by_id.
    """
    unresolved = []
    for i in ids or []:
        if data_store.instance_by_id(i) is None:
            unresolved.append(i)
    return unresolved


def same_scope(
    data_store,
    a_id: str,
    b_id: str,
    scope_classes: list[str],
) -> Optional[bool]:
    """
    True when instances a_id and b_id have a common ancestor of any of the
    listed scope_classes. None when either id doesn't resolve or has no
    matching ancestor — caller decides how to report.

    JSONata equivalent: "X and Y must be within the same <Z>".
    """
    a_parent = data_store.parent_by_klass(a_id, scope_classes)
    b_parent = data_store.parent_by_klass(b_id, scope_classes)
    if a_parent is None or b_parent is None:
        return None
    return a_parent["id"] == b_parent["id"]


def scope_of(data_store, instance_id: str, scope_classes: list[str]) -> Optional[dict]:
    """Thin alias for DataStore.parent_by_klass, for readability in generated code."""
    return data_store.parent_by_klass(instance_id, scope_classes)

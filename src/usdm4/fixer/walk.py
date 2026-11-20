from dataclasses import dataclass

from usdm4.fixer.references import REFERENCES, SUB_CLASSES

SUPER_CLASS = {sub: sup for sup, subs in SUB_CLASSES.items() for sub in subs}


@dataclass
class Instance:
    """A dict in the JSON with a string id and instanceType, and its JSONPath."""

    node: dict
    klass: str
    path: str


def instances(data) -> list[Instance]:
    """Every instance in document order. Paths use the DDF00083 style,
    ``$.study.versions[0].organizations[0].type``."""
    found = []
    _collect(data, "$", found)
    return found


def _collect(node, path: str, found: list) -> None:
    if isinstance(node, dict):
        iid = node.get("id")
        itype = node.get("instanceType")
        if isinstance(iid, str) and isinstance(itype, str):
            found.append(Instance(node, itype, path))
        for key, child in node.items():
            _collect(child, f"{path}.{key}", found)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _collect(child, f"{path}[{index}]", found)


def concrete(klasses) -> set[str]:
    """Target classes with superclasses replaced by their subclasses, so a
    reference to ScheduledInstance matches a ScheduledActivityInstance."""
    result = set()
    pending = list(klasses)
    while pending:
        klass = pending.pop()
        if klass in SUB_CLASSES:
            pending.extend(SUB_CLASSES[klass])
        else:
            result.add(klass)
    return result


def reference_attributes(klass: str) -> dict[str, set[str]]:
    """The id-reference attributes of a class, its own and its superclasses',
    each with its concrete target classes."""
    result = {}
    current = klass
    while current:
        for attribute, targets in REFERENCES.get(current, {}).items():
            result.setdefault(attribute, concrete(targets))
        current = SUPER_CLASS.get(current)
    return result


def super_classes(klass: str) -> list[str]:
    """The class then its superclasses, nearest first."""
    result = [klass]
    while klass in SUPER_CLASS:
        klass = SUPER_CLASS[klass]
        result.append(klass)
    return result

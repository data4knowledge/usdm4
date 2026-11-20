import re
from collections import defaultdict
from dataclasses import dataclass

from usdm4.fixer.fix_result import FixResult
from usdm4.fixer.walk import Instance, instances, reference_attributes

STEP = "ids"
REF_TAG_RE = re.compile(r"<usdm:ref\b[^>]*>")
TAG_ID_RE = re.compile(r'\bid="([^"]*)"')
TAG_KLASS_RE = re.compile(r'\bklass="([^"]*)"')
# Characters allowed in an id: RFC 3986 unreserved, less "~". Anything else
# (spaces, "^", "/", ...) breaks ids used in URIs, e.g. urn:...:{id}.
UNSAFE_RE = re.compile(r"[^A-Za-z0-9_.\-]+")


@dataclass
class Reference:
    """A pointer to an id: an id-reference attribute (one list entry or a
    single value) or a usdm:ref tag in a text attribute. ``targets`` is the
    set of classes it may point at, None when a tag names no klass."""

    owner: Instance
    attribute: str
    index: int | None
    value: str
    targets: set[str] | None
    text: bool

    @property
    def path(self) -> str:
        suffix = "" if self.index is None else f"[{self.index}]"
        return f"{self.owner.path}.{self.attribute}{suffix}"

    def may_point_at(self, klass: str) -> bool:
        return self.targets is None or klass in self.targets


class IdFixer:
    """Make every id in the file unique.

    For an id used more than once:

    - Different classes: the class of the first occurrence keeps the id, the
      others are renumbered and the references to them rewritten. A reference
      is matched to its object through its target classes (from the model) or,
      for a usdm:ref tag, its klass. If a reference could point at more than
      one of the classes sharing the id, nothing is changed for that id.
    - Same class, not referenced: the first keeps the id, the others are
      renumbered.
    - Same class, referenced: an input error. Reported, nothing changed.

    New ids are ``<id>_2``, ``<id>_3`` and so on, skipping any already used.

    Then every id that is unique but not URI-safe (DDF00260 and anything
    outside letters, digits, ``_``, ``.`` and ``-``) has each run of unsafe
    characters replaced by ``_``, for example ``10^12/L`` -> ``10_12_L``,
    with the references following. An id still shared after the first pass
    (a reported input error) is changed the same way on every object that
    has it and every reference to it, so it stays a reported duplicate but
    is URI-safe.
    """

    def __init__(self, result: FixResult):
        self._result = result
        self._used: set[str] = set()

    def fix(self) -> None:
        self._fix_duplicates()
        self._fix_unsafe()

    def _fix_duplicates(self) -> None:
        found = instances(self._result.data)
        self._used = {i.node["id"] for i in found}
        by_id = defaultdict(list)
        for instance in found:
            by_id[instance.node["id"]].append(instance)
        duplicates = {k: v for k, v in by_id.items() if len(v) > 1}
        if not duplicates:
            return
        references = defaultdict(list)
        for ref in self._references(found):
            if ref.value in duplicates:
                references[ref.value].append(ref)
        renames = {}
        for iid, occurrences in duplicates.items():
            renames.update(self._fix_id(iid, occurrences, references[iid]))
        self._rewrite(renames, [r for refs in references.values() for r in refs])

    def _fix_unsafe(self) -> None:
        found = instances(self._result.data)
        self._used = {i.node["id"] for i in found}
        by_id = defaultdict(list)
        for instance in found:
            if UNSAFE_RE.search(instance.node["id"]):
                by_id[instance.node["id"]].append(instance)
        renames = {}
        for old, group in by_id.items():
            base = UNSAFE_RE.sub("_", old).strip("_") or "id"
            if base in self._used:
                new_id = self._new_id(base)
            else:
                new_id = base
                self._used.add(new_id)
            for instance in group:
                instance.node["id"] = new_id
                self._result.change(
                    STEP,
                    instance.path,
                    instance.klass,
                    "id",
                    old,
                    new_id,
                    "id not URI-safe",
                )
                renames[(old, instance.klass)] = new_id
        if renames:
            refs = [r for r in self._references(found) if r.value in by_id]
            self._rewrite(renames, refs)

    def _fix_id(self, iid: str, occurrences: list, refs: list) -> dict:
        """Renumber the occurrences of one id. Returns the (id, class) pairs
        whose references must follow, mapped to the new id."""
        by_klass = defaultdict(list)
        for instance in occurrences:
            by_klass[instance.klass].append(instance)
        klasses = list(by_klass)
        if len(klasses) > 1:
            for ref in refs:
                hits = [k for k in klasses if ref.may_point_at(k)]
                if len(hits) > 1:
                    self._result.issue(
                        STEP,
                        ref.path,
                        ref.owner.klass,
                        ref.attribute,
                        iid,
                        f"id {iid!r} is used by {', '.join(klasses)} and this "
                        f"reference could point at {', '.join(hits)}; "
                        "id left unchanged",
                    )
                    return {}
        keeper = occurrences[0].klass
        renames = {}
        for klass, group in by_klass.items():
            referenced = [r for r in refs if r.may_point_at(klass)]
            if len(group) > 1 and referenced:
                for instance in group:
                    self._result.issue(
                        STEP,
                        instance.path,
                        klass,
                        "id",
                        iid,
                        f"id {iid!r} is used by {len(group)} {klass} instances "
                        f"and referenced {len(referenced)} time(s) "
                        f"(e.g. {referenced[0].path}); input error, left unchanged",
                    )
                continue
            to_rename = group[1:] if klass == keeper else group
            for instance in to_rename:
                new_id = self._new_id(iid)
                instance.node["id"] = new_id
                self._result.change(
                    STEP,
                    instance.path,
                    klass,
                    "id",
                    iid,
                    new_id,
                    "duplicate id" if klass == keeper else f"id also used by {keeper}",
                )
                if len(group) == 1 and referenced:
                    renames[(iid, klass)] = new_id
        return renames

    def _new_id(self, iid: str) -> str:
        n = 2
        while f"{iid}_{n}" in self._used:
            n += 1
        new_id = f"{iid}_{n}"
        self._used.add(new_id)
        return new_id

    def _references(self, found: list) -> list[Reference]:
        refs = []
        for instance in found:
            attributes = reference_attributes(instance.klass)
            for key, value in instance.node.items():
                if key in attributes:
                    targets = attributes[key]
                    if isinstance(value, str):
                        refs.append(
                            Reference(instance, key, None, value, targets, False)
                        )
                    elif isinstance(value, list):
                        for index, item in enumerate(value):
                            if isinstance(item, str):
                                refs.append(
                                    Reference(
                                        instance, key, index, item, targets, False
                                    )
                                )
                elif isinstance(value, str) and "<usdm:ref" in value:
                    for tag in REF_TAG_RE.findall(value):
                        id_match = TAG_ID_RE.search(tag)
                        if not id_match:
                            continue
                        klass_match = TAG_KLASS_RE.search(tag)
                        targets = {klass_match.group(1)} if klass_match else None
                        refs.append(
                            Reference(
                                instance, key, None, id_match.group(1), targets, True
                            )
                        )
        return refs

    def _rewrite(self, renames: dict, refs: list) -> None:
        if not renames:
            return
        texts = set()
        for ref in refs:
            if ref.text:
                texts.add((id(ref.owner.node), ref.attribute))
                continue
            new_id = next(
                (
                    renames[(ref.value, k)]
                    for k in ref.targets
                    if (ref.value, k) in renames
                ),
                None,
            )
            if new_id is None:
                continue
            if ref.index is None:
                ref.owner.node[ref.attribute] = new_id
            else:
                ref.owner.node[ref.attribute][ref.index] = new_id
            self._result.change(
                STEP,
                ref.path,
                ref.owner.klass,
                ref.attribute,
                ref.value,
                new_id,
                "reference follows changed id",
            )
        done = set()
        for ref in refs:
            key = (id(ref.owner.node), ref.attribute)
            if not ref.text or key not in texts or key in done:
                continue
            done.add(key)
            self._rewrite_text(ref.owner, ref.attribute, renames)

    def _rewrite_text(self, owner: Instance, attribute: str, renames: dict) -> None:
        old_text = owner.node[attribute]

        def replace(match: re.Match) -> str:
            tag = match.group(0)
            id_match = TAG_ID_RE.search(tag)
            klass_match = TAG_KLASS_RE.search(tag)
            if not id_match:
                return tag
            old_id = id_match.group(1)
            if klass_match:
                new_id = renames.get((old_id, klass_match.group(1)))
            else:
                # No klass: follow only when the id has one new value.
                hits = {v for (i, _), v in renames.items() if i == old_id}
                new_id = hits.pop() if len(hits) == 1 else None
            if new_id is None:
                return tag
            return tag[: id_match.start(1)] + new_id + tag[id_match.end(1) :]

        new_text = REF_TAG_RE.sub(replace, old_text)
        if new_text != old_text:
            owner.node[attribute] = new_text
            self._result.change(
                STEP,
                f"{owner.path}.{attribute}",
                owner.klass,
                attribute,
                old_text,
                new_text,
                "usdm:ref follows changed id",
            )

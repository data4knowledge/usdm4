"""House-style names for the timeline assembler — issue 63, part 63.4.

Moved out of ``TimelineAssembler`` unchanged in behaviour: epoch names from the
C99079 house terms, activity short names, instance names, and the registries
that keep every one of them unique across a study. One ``Naming`` per
assembly; ``TimelineAssembler.clear`` makes a fresh one.
"""

import re
from pathlib import Path

_HOUSE_NAMES_PATH = Path(__file__).parent.parent / "data" / "house_names.yaml"


class Naming:
    _house_names: dict | None = None

    _ACT_STOPWORDS = {
        "of", "the", "and", "or", "a", "an", "for", "to", "in", "at", "by",
        "with", "per", "on", "from", "if",
    }  # fmt: skip

    _SAI_TEXT_PATTERNS = (
        (re.compile(r"^day\s*(-?\d+)$", re.IGNORECASE), "D{}"),
        (re.compile(r"^week\s*(-?\d+)$", re.IGNORECASE), "W{}"),
        (re.compile(r"^cycle\s*(\d+)[ ,]*day\s*(-?\d+)$", re.IGNORECASE), "C{}D{}"),
    )

    _UNIT_PREFIXES = {
        "day": "D",
        "d": "D",
        "week": "W",
        "wk": "W",
        "w": "W",
        "hour": "H",
        "hr": "H",
        "h": "H",
        "minute": "MIN",
        "min": "MIN",
        "month": "MTH",
        "mth": "MTH",
        "year": "Y",
        "yr": "Y",
        "y": "Y",
    }

    def __init__(self):
        # SAI names are derived from timing/visit text (D1, W12, SCREENING) so
        # the timing sheet's from/to references are human-readable. The
        # registry keeps them unique across every timeline in the study.
        self._sai_name_registry: dict[str, int] = {}
        self._activity_name_registry: dict[str, str] = {}
        # Epoch names come from the CT epoch terms, which are deliberately
        # many-to-one: two screening periods, or three treatment cycles, all
        # ask for the same house name. Registered under the QUALIFIED name, so
        # `T1-SCR` and `T2-SCR` remain distinct in a multi-timeline study.
        self._epoch_name_registry: dict[str, str] = {}
        self.multi_timeline: bool = False

    # ------------------------------------------------------------------
    # Shared helpers

    def qualify(self, name: str, t: int) -> str:
        """House style: `E1` in a single-timeline study, `T2-E1` where several
        timelines are built. Prefixing unconditionally makes every identifier
        in the common case four characters longer for no gain."""
        return f"T{t}-{name}" if self.multi_timeline else name

    @classmethod
    def house(cls) -> dict:
        """The curated short-name vocabulary, loaded once.

        `data/house_names.yaml` is meant to be added to: an entry there beats
        the generated form, so curating a name is how an ugly one gets fixed.
        A missing or unreadable file degrades to generation for everything
        rather than failing the assembly."""
        if cls._house_names is None:
            try:
                import yaml

                cls._house_names = yaml.safe_load(_HOUSE_NAMES_PATH.read_text()) or {}
            except Exception:
                cls._house_names = {}
        return cls._house_names

    @staticmethod
    def name_key(text: str) -> str:
        """Lookup key: case, punctuation, whitespace and a trailing footnote
        marker all removed. `Pregnancy Test`, `pregnancy test` and
        `Pregnancy testb` resolve to the same entry."""
        t = (text or "").strip().lower()
        t = re.sub(r"[\s,;]*\(?[a-z]?\d{1,2}\)?$", "", t)
        t = re.sub(r"[^a-z0-9/ -]+", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    @staticmethod
    def identity(text: str) -> str:
        """What counts as the SAME thing when deciding a name is taken.

        Surrounding whitespace and case, nothing else. Deliberately NOT
        ``name_key``, which strips a trailing number: that is right for a
        house-name lookup and wrong for identity, because it makes `Cycle 1`
        and `Cycle 2` — two real epochs — indistinguishable.
        """
        return (text or "").strip().casefold()

    def significant_words(self, text: str) -> list[str]:
        return [
            w
            for w in re.split(r"[^A-Za-z0-9]+", text or "")
            if w and w.lower() not in self._ACT_STOPWORDS
        ]

    def initials(self, text: str) -> str:
        """Initials of the significant words, uppercased and capped. A single
        word gives its first four characters."""
        words = self.significant_words(text)
        if not words:
            return ""
        return (
            words[0][:4] if len(words) == 1 else "".join(w[0] for w in words)[:6]
        ).upper()

    # ------------------------------------------------------------------
    # Epochs

    def epoch_name(self, label: str, index: int) -> str:
        """House-style epoch name.

        Matched against the CDISC C99079 (SDTM Epoch) terms in
        `data/house_names.yaml` — SCREENING -> `SCR`, FOLLOW-UP -> `FU` — so
        the same phase carries the same name across protocols however the
        document words it. Unmatched epochs generate from the label.

        The result is the house name for this label alone and may already be
        held by another epoch in the same study — the matching is many-to-one
        by design. `claim_epoch_name` is what makes it unique; call it on the
        qualified form, never use this on its own."""
        key = self.name_key(label)
        if key:
            pairs = [
                (c, term["name"])
                for term in (self.house().get("epochs") or {}).values()
                for c in (term.get("match") or [])
            ]
            # Longest candidate first: `long-term follow-up` must not be taken
            # by `follow-up`, which it ends with.
            for candidate, name in sorted(pairs, key=lambda x: -len(x[0])):
                if (
                    key == candidate
                    or key.startswith(candidate + " ")
                    or key.endswith(" " + candidate)
                ):
                    return name
            # No CT term fits — generate the same way an activity does, rather
            # than truncating a slug mid-word (`BONEMARROWSU`).
            return self.initials(label) or f"EP{index}"
        return f"EP{index}"

    def claim_epoch_name(self, name: str, label: str) -> str:
        """Claim ``name`` for ``label``, or the next free ordinal of it.

        A name is a cross-reference key and has to be unique within the study,
        however it was arrived at. Two epochs labelled `Period I - Screening`
        and `Period II - Screening` both resolve to `SCR`; without this the
        second raises a duplicate cross-reference in the builder and the
        failure propagates until the study itself comes back None.

        **Only a DIFFERENT epoch takes an ordinal.** Asking again for a name
        already held by the same label hands back that same name. The ordinal
        goes on the LOSER, never the holder.
        """
        taken = self._epoch_name_registry
        identity = self.identity(label)
        if taken.get(name, identity) == identity:
            taken[name] = identity
            return name
        ordinal = 2
        while f"{name}{ordinal}" in taken:
            ordinal += 1
        taken[f"{name}{ordinal}"] = identity
        return f"{name}{ordinal}"

    # ------------------------------------------------------------------
    # Activities

    def activity_name(self, text: str, seq: int) -> str:
        """House style short name for an activity: `VS`, `IC`, `ECG`.

        `name` is a shorthand identifier — short, unique, and meaningful enough
        to follow a cross-reference by eye. The protocol's own wording is the
        `label`. Derivation is initials of the significant words (one word
        gives its first four characters). A collision extends the abbreviation
        from the word that diverges rather than appending a number:
        `physical examination` -> `PE`, `participant education` -> `PEDU`.

        A curated name can collide too, by design (`house_names.yaml` maps
        synonyms onto one name). The first label to ask keeps it; a later one
        with different text is named as though it were not curated.
        """
        raw = (text or "").strip()
        if not raw:
            return f"ACT{seq}"
        table = self.house().get("activities") or {}
        key = self.name_key(raw)
        curated = table.get(key)
        if curated is None and len(key) > 4 and key[-1].isalpha():
            # `Pregnancy testb` — a footnote LETTER. Only consulted to find a
            # curated entry; the text itself is never rewritten.
            curated = table.get(key[:-1].strip())
        taken = self._activity_name_registry
        me = self.identity(raw)
        if curated and taken.get(curated, me) == me:
            taken[curated] = me
            return curated
        words = self.significant_words(raw)
        if not words:
            return f"ACT{seq}"
        base = self.initials(raw)
        if base not in taken:
            taken[base] = me
            return base
        if taken[base] == me:
            return base
        for extra in range(1, 4):  # PE -> PEDU -> PEDUC
            longer = "".join(w[: 1 + extra] for w in words)[:8].upper()
            if longer not in taken:
                taken[longer] = me
                return longer
        n = 2
        while f"{base}{n}" in taken:
            n += 1
        taken[f"{base}{n}"] = me
        return f"{base}{n}"

    # ------------------------------------------------------------------
    # Scheduled activity instances

    def sai_name(
        self,
        timing_text: str | None,
        timing_value: int | None,
        timing_unit: str | None,
        visit_text: str | None,
        t: int,
        index: int,
        cycle: int | None = None,
    ) -> str:
        """Human-readable SAI name for the timing sheet's from/to references.
        In a single-cycle column with a day timing, from the parsed cycle and
        day (``cycle=2``, ``Day 8`` → ``C2D8``, issue 66); otherwise derived
        from the timing text (``Day 1`` → ``D1``, ``Week 12`` → ``W12``,
        ``Cycle 2 Day 1`` → ``C2D1``), else an upper-cased slug of the timing
        or visit text, else the positional fallback ``T{t}-SAI-{n}``. Uniqued
        across the study with a numeric suffix."""
        if cycle is not None and timing_value is not None and timing_unit == "day":
            base = f"C{cycle}D{timing_value}"
        else:
            base = self._sai_base_name(
                timing_text, timing_value, timing_unit, visit_text
            )
        return self._register_sai(base or f"T{t}-SAI-{index + 1}")

    def decision_name(self, cycle: str | int | None, t: int) -> str:
        """A cycle range's decision (issue 69): ``C3+DEC``. Uniqued across
        the study with the SAI names."""
        return self._register_sai(f"C{cycle}DEC" if cycle is not None else f"T{t}-DEC")

    def end_name(self, t: int) -> str:
        """The end instance after a range that is the last column (issue
        69): ``T1-END``."""
        return self._register_sai(f"T{t}-END")

    def _register_sai(self, base: str) -> str:
        count = self._sai_name_registry.get(base, 0) + 1
        self._sai_name_registry[base] = count
        return base if count == 1 else f"{base}-{count}"

    def _sai_base_name(
        self,
        timing_text: str | None,
        timing_value: int | None,
        timing_unit: str | None,
        visit_text: str | None,
    ) -> str:
        for source, text in (
            ("timing", timing_text or ""),
            ("visit", visit_text or ""),
        ):
            text = text.strip()
            if not text:
                continue
            if source == "timing" and re.fullmatch(r"[+-]?\d+", text):
                # A bare number is a day/week count — prefix with the unit
                # letter, preferring the signed value (the text often drops
                # the sign).
                unit = (timing_unit or "").strip().lower().rstrip("s")
                prefix = self._UNIT_PREFIXES.get(unit)
                if prefix:
                    value = timing_value
                    return f"{prefix}{value if value is not None else text}"
            for pattern, template in self._SAI_TEXT_PATTERNS:
                match = pattern.match(text)
                if match:
                    return template.format(*match.groups())
            slug = re.sub(r"[^A-Z0-9+,_ .-]", "", text.upper().replace("/", " "))
            slug = re.sub(r"\s+", " ", slug).strip()
            if slug:
                return slug[:20].rstrip()
        return ""

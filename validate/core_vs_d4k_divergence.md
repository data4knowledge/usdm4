# CORE-only divergence punch list

12 rules where the CDISC CORE engine flagged a failure against `validate/sample_usdm.json` but d4k's implementation returned Success. For each rule, the DDF text and severity, the CORE condition and the CORE message on this sample, and the current d4k `validate()` body, followed by a read on what likely needs to change.

Generated against `~/Library/Caches/usdm4/core/rules/usdm/4-0.json` and the current `src/usdm4/rules/library/` on this branch. The sample-specific finding counts come from the existing `validate/sample_usdm_*.yaml` run — regenerate after changes to confirm.

## DDF00012

**DDF text.** Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

**Severity.** ERROR  |  **Entity.** ScheduleTimeline  |  **Attributes.** mainTimeline  |  **Check id.** CHK0030

**CORE id.** `CORE-000407`  |  **rule_type.** JSONata  |  **executability.** fully executable

**CORE conditions.**

```yaml
"$.study.versions.studyDesigns.\n  {\n      \"instanceType\": instanceType,\n      \"id\": id,\n      \"path\": _path,\n \
  \     \"name\": name,\n      \"# Main timelines\": $count(scheduleTimelines[mainTimeline=true]),\n      \"Main timelines\"\
  : scheduleTimelines[mainTimeline=true]\n                        ~> $map(function($v){$v.id & ($v.name ? \" [\" & $v.name\
  \ & \"]\")})\n  }[`# Main timelines` != 1][]"
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The study design does not have exactly one main timeline.
```

**CORE on sample.** 1 finding(s) — 'The study design does not have exactly one main timeline.'

**Current d4k implementation.**

```python
# MANUAL: do not regenerate
#
# Cardinality rule: exactly one ScheduleTimeline per StudyDesign must have
# mainTimeline=True. CORE JSONata iterates studyDesigns and filters on
# scheduleTimelines[mainTimeline=true]. Implemented here via DataStore —
# iterate the concrete StudyDesign subclasses and access their embedded
# scheduleTimelines list directly.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00012(RuleTemplate):
    """
    DDF00012: Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

    Applies to: ScheduleTimeline
    Attributes: mainTimeline
    """

    def __init__(self):
        super().__init__(
            "DDF00012",
            RuleTemplate.ERROR,
            "Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                count = sum(
                    1
                    for t in (sd.get("scheduleTimelines") or [])
                    if t.get("mainTimeline") is True
                )
                if count != 1:
                    self._add_failure(
                        f"Expected exactly one main ScheduleTimeline in study design, found {count}",
                        sd_cls,
                        "scheduleTimelines",
                        data.path_by_id(sd["id"]),
                    )
        return self._result()
```

**Likely divergence.** d4k iterates only `InterventionalStudyDesign` and `ObservationalStudyDesign` via `instances_by_klass`. If the sample registers its study design under the base `StudyDesign` class name (or its DataStore indexes by a different key), the loop runs zero times and `_result()` returns True vacuously. Confirm by logging how many StudyDesign-family instances the data store exposes on this sample, then widen `STUDY_DESIGN_CLASSES` or resolve via DataStore's inheritance-aware lookup.

---

## DDF00017

**DDF text.** Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).

**Severity.** ERROR  |  **Entity.** SubjectEnrollment  |  **Attributes.** quantity  |  **Check id.** CHK0021

**CORE id.** `CORE-000806`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: Quantity
    target: instanceType
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: equal_to
  value:
    comparator: SubjectEnrollment
    target: parent_entity
- name: get_dataset
  operator: equal_to
  value:
    comparator: quantity
    target: parent_rel
- not:
    any:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: false
        target: unit
    - name: get_dataset
      operator: not_exists
      value:
        comparator: null
        target: unit
    - name: get_dataset
      operator: empty
      value:
        comparator: null
        target: unit
    - all:
      - name: get_dataset
        operator: equal_to
        value:
          comparator: http://www.cdisc.org
          target: unit.standardCode.codeSystem
      - name: get_dataset
        operator: equal_to
        value:
          comparator: C25613
          target: unit.standardCode.code
      - name: get_dataset
        operator: equal_to
        value:
          comparator: '%'
          target: unit.standardCode.decode
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The unit for a subject enrollement quantity is not empty or coded as % (codeSystem = http://www.cdisc.org, code
      = C25613 and decode = %).
```

**CORE on sample.** 1 finding(s) — 'The unit for a subject enrollement quantity is not empty or coded as % (codeSystem = http://www.cdisc.org, code = C25613 and decode = %).'

**Current d4k implementation.**

```python
# MANUAL: do not regenerate
#
# SubjectEnrollment.quantity is an embedded Quantity. Its unit must be
# absent/empty OR a Percent code (C25613). CORE accepts false / null /
# missing for the unit and an embedded Code with code == "C25613".
from usdm4.rules.rule_template import RuleTemplate


PERCENT_CODE = "C25613"


def _is_acceptable_unit(unit):
    if unit is None or unit is False:
        return True
    if not isinstance(unit, dict):
        return False
    if not unit:
        return True
    standard = unit.get("standardCode")
    if isinstance(standard, dict) and standard.get("code") == PERCENT_CODE:
        return True
    return False


class RuleDDF00017(RuleTemplate):
    """
    DDF00017: Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).

    Applies to: SubjectEnrollment
    Attributes: quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00017",
            RuleTemplate.ERROR,
            "Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for enrollment in data.instances_by_klass("SubjectEnrollment"):
            quantity = enrollment.get("quantity")
            if not isinstance(quantity, dict):
                continue
            if not _is_acceptable_unit(quantity.get("unit")):
                self._add_failure(
                    "SubjectEnrollment.quantity has a unit that is neither empty nor Percent (C25613)",
                    "SubjectEnrollment",
                    "quantity",
                    data.path_by_id(enrollment["id"]),
                )
        return self._result()
```

**Likely divergence.** Implementation looks structurally right — iterates SubjectEnrollment, reads quantity.unit, calls `_is_acceptable_unit`. Check the helper: CORE considers the unit acceptable if it's empty OR the `%` code. If the helper is comparing against a specific C-code (e.g. C25613 Percent) but the sample uses a different representation (e.g. the literal '%' string, or a different codelist term), it passes incorrectly. Verify the helper against the sample's actual unit field.

---

## DDF00041

**DDF text.** Within a study design, there must be at least one endpoint with level primary.

**Severity.** ERROR  |  **Entity.** Endpoint  |  **Attributes.** level  |  **Check id.** CHK0036

**CORE id.** `CORE-001036`  |  **rule_type.** JSONata  |  **executability.** fully executable

**CORE conditions.**

```yaml
"$.study.versions.studyDesigns.\n  {\n      \"instanceType\": instanceType,\n      \"id\": id,\n      \"path\": _path,\n \
  \     \"name\": name,\n      \"# Primary endpoints\": $count(objectives.endpoints[level.code=\"C94496\"])\n  }[`# Primary\
  \ endpoints` = 0][]"
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: There is not at least one endpoint with a level of primary within the study design.
```

**CORE on sample.** 1 finding(s) — 'There is not at least one endpoint with a level of primary within the study design.'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00041(RuleTemplate):
    """
    DDF00041: Within a study design, there must be at least one endpoint with level primary.

    Applies to: Endpoint
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00041",
            RuleTemplate.ERROR,
            "Within a study design, there must be at least one endpoint with level primary.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Endpoint"):
            if not item.get("level"):
                self._add_failure(
                    "Required attribute 'level' is missing or empty",
                    "Endpoint",
                    "level",
                    data.path_by_id(item["id"]),
                )
        return self._result()
```

**Likely divergence.** **Semantic bug.** Current code checks that every Endpoint has *some* level set. It does NOT check whether any endpoint has level=Primary. DDF text says: at least one endpoint must be level Primary. The implementation is answering a different question. Rewrite: iterate Endpoints, count those where the level code matches the Primary C-code, fail if count < 1.

---

## DDF00083

**DDF text.** Within a study version, all id values must be unique.

**Severity.** ERROR  |  **Entity.** All  |  **Attributes.** id  |  **Check id.** CHK0005

**CORE id.** `CORE-001015`  |  **rule_type.** JSONata  |  **executability.** fully executable

**CORE conditions.**

```yaml
"(\n  **.*[id and instanceType].\n    {\n      \"id\": id,\n      \"details\":\n        {\n          \"instanceType\": instanceType,\n\
  \          \"id\": id, \n          \"path\": _path,\n          \"name\": name\n        }\n    }.${id: details}\n  ~> $sift(function($v){$count($v)\
  \ > 1})\n).*"
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The id value is not unique.
```

**CORE on sample.** 4 finding(s) — 'The id value is not unique.'

**Current d4k implementation.**

```python
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
        # See rule DDF00082 for schema checks
        return True
```

**Likely divergence.** **Stub.** Implementation is literally `return True`. The comment says 'See rule DDF00082 for schema checks' but DDF00082 is a schema-shape rule, not a uniqueness rule. This rule needs to be written: iterate every indexed instance in the data store, group by `id`, fail any id with >1 instance. DataStore should already expose `_ids` or equivalent (see DDF00010 for the grouping pattern).

---

## DDF00084

**DDF text.** Within a study design there must be exactly one objective with level 'Primary Objective'.

**Severity.** ERROR  |  **Entity.** Objective  |  **Attributes.** level  |  **Check id.** CHK0035

**CORE id.** `CORE-000871`  |  **rule_type.** Record Data  |  **executability.** partially executable - possible overreporting

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- not:
    all:
    - name: get_dataset
      operator: non_empty
      value:
        comparator: null
        target: $num_primary_obj
    - name: get_dataset
      operator: equal_to
      value:
        comparator: 1
        target: $num_primary_obj
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: There is not exactly one objective with a level of 'Primary Objective' within the study design.
```

**CORE on sample.** 1 finding(s) — "There is not exactly one objective with a level of 'Primary Objective' within the study design."

**Current d4k implementation.**

```python
# MANUAL: do not regenerate
#
# Cardinality rule: exactly one Primary Objective per StudyDesign. No CORE
# JSONata was provided (the rule isn't in the CORE JSON for v4) — rule text
# is unambiguous. "Primary Objective" is CDISC code C94496 (see
# rule_ddf00096 which uses the same code for the primary objective filter).
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]
PRIMARY_OBJECTIVE_CODE = "C94496"


class RuleDDF00084(RuleTemplate):
    """
    DDF00084: Within a study design there must be exactly one objective with level 'Primary Objective'.

    Applies to: Objective
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00084",
            RuleTemplate.ERROR,
            "Within a study design there must be exactly one objective with level 'Primary Objective'.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                count = 0
                for obj in sd.get("objectives") or []:
                    level = obj.get("level") or {}
                    if isinstance(level, dict) and level.get("code") == PRIMARY_OBJECTIVE_CODE:
                        count += 1
                if count != 1:
                    self._add_failure(
                        f"Expected exactly one Primary Objective in study design, found {count}",
                        sd_cls,
                        "objectives",
                        data.path_by_id(sd["id"]),
                    )
        return self._result()
```

**Likely divergence.** Same failure mode as DDF00012 — iterates only the two concrete StudyDesign subclasses via `instances_by_klass`. Loop runs zero times → `_result()` returns True. Fix strategy identical: broaden class resolution. Separately, the code compares `level.code == PRIMARY_OBJECTIVE_CODE` — verify that constant matches the CT code the sample actually uses.

---

## DDF00114

**DDF text.** If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.

**Severity.** ERROR  |  **Entity.** Condition  |  **Attributes.** context  |  **Check id.** CHK0127

**CORE id.** `CORE-000878`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: contextIds
    target: parent_rel
    value_is_literal: true
- name: get_dataset
  operator: non_empty
  value:
    comparator: null
    target: $condition_count
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The specified context of the condition is not a valid instance of either the Activity or ScheduledActivityInstance
      class (the value of the condition's contextIds attribute either matches the id of an instance that is not an Activity
      or ScheduledActivityInstance, or it does not match the id of any class instance).
```

**CORE on sample.** 24 finding(s) — "The specified context of the condition is not a valid instance of either the Activity or ScheduledActivityInstance class (the value of the condition's contextIds attribute either matches the id of an instance that is not an Activity or ScheduledActivityInstance, or it does not match the id of any class instance)."

**Current d4k implementation.**

```python
# MANUAL: do not regenerate
#
# Condition.contextIds is a list of FK strings that must each resolve
# to an existing instance whose instanceType is Activity or
# ScheduledActivityInstance. The failure covers both cases: the id
# doesn't exist, OR it exists but points to the wrong class.
from usdm4.rules.rule_template import RuleTemplate


ALLOWED_CONTEXT_CLASSES = {"Activity", "ScheduledActivityInstance"}


class RuleDDF00114(RuleTemplate):
    """
    DDF00114: If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.

    Applies to: Condition
    Attributes: contextIds
    """

    def __init__(self):
        super().__init__(
            "DDF00114",
            RuleTemplate.ERROR,
            "If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for condition in data.instances_by_klass("Condition"):
            for context_id in condition.get("contextIds") or []:
                if not context_id:
                    continue
                target = data.instance_by_id(context_id)
                target_type = target.get("instanceType") if isinstance(target, dict) else None
                if target_type not in ALLOWED_CONTEXT_CLASSES:
                    reason = (
                        "does not resolve to any instance"
                        if target is None
                        else f"resolves to {target_type} (not Activity or ScheduledActivityInstance)"
                    )
                    self._add_failure(
                        f"Condition.contextIds entry {context_id!r} {reason}",
                        "Condition",
                        "contextIds",
                        data.path_by_id(condition["id"]),
                    )
        return self._result()
```

**Likely divergence.** **Attribute name mismatch.** xlsx says the attribute is `context` (singular, a single FK). d4k iterates `condition.get('contextIds')` (plural list). If V4 uses `context` not `contextIds`, the list is always None and the loop body never runs. Check the actual class definition — if `context` is the FK field, the implementation needs to read that single value, not iterate a list. 24 findings in CORE against Pass in d4k is consistent with this — every Condition in the sample has a context, none have contextIds.

---

## DDF00141

**DDF text.** A planned sex must be specified using the Sex of Participants (C66732) SDTM codelist.

**Severity.** ERROR  |  **Entity.** StudyDesignPopulation, StudyCohort  |  **Attributes.** plannedSex  |  **Check id.** CHK0206

**CORE id.** `CORE-000857`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: equal_to
  value:
    comparator: true
    target: plannedSex
- name: get_dataset
  operator: equal_to
  value:
    comparator: plannedSex
    target: parent_rel.Code
    value_is_literal: true
- not:
    all:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: http://www.cdisc.org
        target: codeSystem
    - name: get_dataset
      operator: is_contained_by
      value:
        comparator: $valid_versions
        target: codeSystemVersion
    - any:
      - all:
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $value_for_code
        - any:
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_pref_term
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_value
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_pref_term
              target: code
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_value
              target: code
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $pref_term_for_code
              target: decode
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $value_for_code
              target: decode
      - all:
        - name: get_dataset
          operator: equal_to
          value:
            comparator: true
            target: $codelist_extensible
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_pref_term
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_value
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $value_for_code
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The planned sex is not specified using the Sex of Participants (C66732) SDTM codelist - codeSystem is not "http://www.cdisc.org",
      codeSystemVersion is not a valid terminology package date, the code or decode (either as preferred term or as submission
      value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist
      value (case sensitive), and/or neither code nor decode is found in the codelist.
```

**CORE on sample.** 1 finding(s) — 'The planned sex is not specified using the Sex of Participants (C66732) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive), and/or neither code nor decode is found in the codelist.'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00141(RuleTemplate):
    """
    DDF00141: A planned sex must be specified using the Sex of Participants (C66732) SDTM codelist.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedSex
    """

    def __init__(self):
        super().__init__(
            "DDF00141",
            RuleTemplate.ERROR,
            "A planned sex must be specified using the Sex of Participants (C66732) SDTM codelist.",
        )

    def validate(self, config: dict) -> bool:
        pop_result = self._ct_check(config, "StudyDesignPopulation", "plannedSex")
        cohort_result = self._ct_check(config, "StudyCohort", "plannedSex")
        return pop_result or cohort_result
```

**Likely divergence.** **Boolean bug.** Returns `pop_result or cohort_result`. `_ct_check` returns True when it found no errors. If the StudyDesignPopulation side passes (True) and the StudyCohort side fails (False), `True or False` = True, so the rule reports Success even though `_add_failure` was called on the cohort side. The accumulated failures ARE present in `self._errors` but the return value lies. Change to `pop_result and cohort_result`, or better: call both, then `return self._result()`.

---

## DDF00142

**DDF text.** A governance date type must be specified according to the extensible governance date type (C207413) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Severity.** ERROR  |  **Entity.** GovernanceDate  |  **Attributes.** type  |  **Check id.** CHK0209

**CORE id.** `CORE-000925`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: exists
  value:
    comparator: null
    target: type
- name: get_dataset
  operator: equal_to
  value:
    comparator: true
    target: type
- not:
    all:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: http://www.cdisc.org
        target: type.codeSystem
    - name: get_dataset
      operator: is_contained_by
      value:
        comparator: $valid_versions
        target: type.codeSystemVersion
    - name: get_dataset
      operator: equal_to
      value:
        comparator: true
        target: $codelist_extensible
    - any:
      - all:
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_pref_term
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_value
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $value_for_code
      - all:
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $value_for_code
        - any:
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_pref_term
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_value
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_pref_term
              target: type.code
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_value
              target: type.code
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $pref_term_for_code
              target: type.decode
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $value_for_code
              target: type.decode
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The governance date type is not specified according to the extensible governance date type (C207413) DDF codelist
      - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code
      or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding
      decode or code does not match the codelist value (case sensitive).
```

**CORE on sample.** 2 finding(s) — 'The governance date type is not specified according to the extensible governance date type (C207413) DDF codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive).'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00142(RuleTemplate):
    """
    DDF00142: A governance date type must be specified according to the extensible governance date type (C207413) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: GovernanceDate
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00142",
            RuleTemplate.ERROR,
            "A governance date type must be specified according to the extensible governance date type (C207413) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "GovernanceDate", "type")
```

**Likely divergence.** One-liner CT check — `_ct_check(config, 'GovernanceDate', 'type')`. CORE caught 2 findings. Options: (a) the `_ct_check` helper on extensible codelists is too permissive or too strict relative to CORE's condition; (b) attribute drift — d4k looks at `GovernanceDate.type` but the sample stores the type elsewhere; (c) the resolved codelist in `CTLibrary` for this class/attribute pair is different from what CORE uses. Log the codes/decodes `_ct_check` is comparing against on this sample and cross-check with the C207413 contents.

---

## DDF00143

**DDF text.** A study amendment reason must be coded using the study amendment reason (C207415) DDF codelist.

**Severity.** ERROR  |  **Entity.** StudyAmendmentReason  |  **Attributes.** code  |  **Check id.** CHK0210

**CORE id.** `CORE-000930`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: exists
  value:
    comparator: null
    target: code
- name: get_dataset
  operator: equal_to
  value:
    comparator: true
    target: code
- not:
    all:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: http://www.cdisc.org
        target: code.codeSystem
    - name: get_dataset
      operator: is_contained_by
      value:
        comparator: $valid_versions
        target: code.codeSystemVersion
    - any:
      - all:
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $value_for_code
        - any:
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_pref_term
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_value
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_pref_term
              target: code.code
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_value
              target: code.code
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $pref_term_for_code
              target: code.decode
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $value_for_code
              target: code.decode
      - all:
        - name: get_dataset
          operator: equal_to
          value:
            comparator: true
            target: $codelist_extensible
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_pref_term
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_value
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $value_for_code
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The study amendment reason is not coded using the study amendment reason (C207415) DDF codelist - codeSystem
      is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode
      (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding
      decode or code does not match the codelist value (case sensitive).
```

**CORE on sample.** 2 finding(s) — 'The study amendment reason is not coded using the study amendment reason (C207415) DDF codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive).'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00143(RuleTemplate):
    """
    DDF00143: A study amendment reason must be coded using the study amendment reason (C207415) DDF codelist.

    Applies to: StudyAmendmentReason
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00143",
            RuleTemplate.ERROR,
            "A study amendment reason must be coded using the study amendment reason (C207415) DDF codelist.",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyAmendmentReason", "code")
```

**Likely divergence.** Same shape as DDF00142 — one-liner `_ct_check(config, 'StudyAmendmentReason', 'code')`. 2 findings on CORE. Probably the same class of issue across the 00142/143/144/146 family.

---

## DDF00144

**DDF text.** A study geographic scope type must be specified using the geographic scope type (C207412) DDF codelist.

**Severity.** ERROR  |  **Entity.** GeographicScope  |  **Attributes.** type  |  **Check id.** CHK0211

**CORE id.** `CORE-000931`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: equal_to
  value:
    comparator: true
    target: type
- not:
    all:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: http://www.cdisc.org
        target: type.codeSystem
    - name: get_dataset
      operator: is_contained_by
      value:
        comparator: $valid_versions
        target: type.codeSystemVersion
    - any:
      - all:
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $value_for_code
        - any:
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_pref_term
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_value
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_pref_term
              target: type.code
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_value
              target: type.code
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $pref_term_for_code
              target: type.decode
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $value_for_code
              target: type.decode
      - all:
        - name: get_dataset
          operator: equal_to
          value:
            comparator: true
            target: $codelist_extensible
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_pref_term
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_value
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $value_for_code
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The study geographic scope type is not specified using the geographic scope type (C207412) DDF codelist - codeSystem
      is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, the code or decode (either
      as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or
      code does not match the codelist value (case sensitive), and/or neither code nor decode is found in the codelist.
```

**CORE on sample.** 2 finding(s) — 'The study geographic scope type is not specified using the geographic scope type (C207412) DDF codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive), and/or neither code nor decode is found in the codelist.'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00144(RuleTemplate):
    """
    DDF00144: A study geographic scope type must be specified using the geographic scope type (C207412) DDF codelist.

    Applies to: GeographicScope
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00144",
            RuleTemplate.ERROR,
            "A study geographic scope type must be specified using the geographic scope type (C207412) DDF codelist.",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "GeographicScope", "type")
```

**Likely divergence.** Same shape as DDF00142 — one-liner `_ct_check(config, 'GeographicScope', 'type')`. 2 findings on CORE. Same family.

---

## DDF00146

**DDF text.** A study title type must be specified using the study title type (C207419) DDF codelist.

**Severity.** ERROR  |  **Entity.** StudyTitle  |  **Attributes.** type  |  **Check id.** CHK0213

**CORE id.** `CORE-000933`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- name: get_dataset
  operator: equal_to
  value:
    comparator: true
    target: type
- not:
    all:
    - name: get_dataset
      operator: equal_to
      value:
        comparator: http://www.cdisc.org
        target: type.codeSystem
    - name: get_dataset
      operator: is_contained_by
      value:
        comparator: $valid_versions
        target: type.codeSystemVersion
    - any:
      - all:
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: non_empty
          value:
            comparator: null
            target: $value_for_code
        - any:
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_pref_term
          - name: get_dataset
            operator: non_empty
            value:
              comparator: null
              target: $code_for_decode_value
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_pref_term
              target: type.code
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $code_for_decode_value
              target: type.code
        - any:
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $pref_term_for_code
              target: type.decode
          - name: get_dataset
            operator: equal_to
            value:
              comparator: $value_for_code
              target: type.decode
      - all:
        - name: get_dataset
          operator: equal_to
          value:
            comparator: true
            target: $codelist_extensible
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_pref_term
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $code_for_decode_value
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $pref_term_for_code
        - name: get_dataset
          operator: empty
          value:
            comparator: null
            target: $value_for_code
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The study title type is not specified using the study title type (C207419) DDF codelist - codeSystem is not "http://www.cdisc.org",
      codeSystemVersion is not a valid terminology package date, the code or decode (either as preferred term or as submission
      value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist
      value (case sensitive), and/or neither code nor decode is found in the codelist.
```

**CORE on sample.** 3 finding(s) — 'The study title type is not specified using the study title type (C207419) DDF codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive), and/or neither code nor decode is found in the codelist.'

**Current d4k implementation.**

```python
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00146(RuleTemplate):
    """
    DDF00146: A study title type must be specified using the study title type (C207419) DDF codelist.

    Applies to: StudyTitle
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00146",
            RuleTemplate.ERROR,
            "A study title type must be specified using the study title type (C207419) DDF codelist.",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyTitle", "type")
```

**Likely divergence.** Same shape as DDF00142 — one-liner `_ct_check(config, 'StudyTitle', 'type')`. 3 findings on CORE. Same family. DDF00141–46 all converge on the same underlying `_ct_check` machinery, so investigating 00142 carefully is likely to unlock all five.

---

## DDF00181

**DDF text.** Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.

**Severity.** ERROR  |  **Entity.** StudyDefinitionDocumentVersion  |  **Attributes.** dateValues  |  **Check id.** CHK0207

**CORE id.** `CORE-001068`  |  **rule_type.** Record Data  |  **executability.** fully executable

**CORE conditions.**

```yaml
all:
- name: get_dataset
  operator: equal_to
  value:
    comparator: StudyDefinitionDocumentVersion
    target: instanceType
- name: get_dataset
  operator: equal_to
  value:
    comparator: definition
    target: rel_type
- any:
  - all:
    - name: get_dataset
      operator: exists
      value:
        comparator: null
        target: code.standardCode.code
    - name: get_dataset
      operator: is_not_unique_set
      value:
        comparator:
        - type.code
        - type.code.GeographicScope
        - code.standardCode.code
        target: id
  - all:
    - name: get_dataset
      operator: not_exists
      value:
        comparator: null
        target: code.standardCode.code
    - name: get_dataset
      operator: is_not_unique_set
      value:
        comparator:
        - type.code
        - type.code.GeographicScope
        target: id
```

**CORE actions.**

```yaml
- name: generate_dataset_error_objects
  params:
    message: The study definition document version has more than one governance date with the same type and geographic scope.
```

**CORE on sample.** 1 finding(s) — 'The study definition document version has more than one governance date with the same type and geographic scope.'

**Current d4k implementation.**

```python
# MANUAL: do not regenerate
#
# Twin of DDF00093 scoped to StudyDefinitionDocumentVersion rather
# than StudyVersion. Same (type.code, frozenset(scope codes)) key.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


def _date_key(date):
    type_code = (date.get("type") or {}).get("code") if isinstance(date.get("type"), dict) else None
    scopes = date.get("geographicScopes") or []
    scope_codes = frozenset(
        (s.get("type") or {}).get("code")
        for s in scopes
        if isinstance(s, dict) and isinstance(s.get("type"), dict)
    )
    return (type_code, scope_codes)


class RuleDDF00181(RuleTemplate):
    """
    DDF00181: Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.

    Applies to: StudyDefinitionDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00181",
            RuleTemplate.ERROR,
            "Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sddv in data.instances_by_klass("StudyDefinitionDocumentVersion"):
            groups: dict = defaultdict(list)
            for date in sddv.get("dateValues") or []:
                if not isinstance(date, dict):
                    continue
                key = _date_key(date)
                if key[0] is None:
                    continue
                groups[key].append(date)
            for key, dates in groups.items():
                if len(dates) <= 1:
                    continue
                for date in dates:
                    self._add_failure(
                        f"StudyDefinitionDocumentVersion.dateValues has {len(dates)} entries with type.code {key[0]!r} and geographic scopes {sorted(key[1])}",
                        "GovernanceDate",
                        "type, geographicScopes",
                        data.path_by_id(date["id"]),
                    )
        return self._result()
```

**Likely divergence.** Implementation looks correct structurally — groups dateValues by `(type.code, frozenset(scope codes))` and flags groups > 1. CORE reported 1 finding on the sample. Two hypotheses: (a) the sample's geographicScopes list is absent on some dates, so all-empty-scope entries collide the way CORE sees it but d4k's frozenset(None) behaviour differs; (b) the `date.get('type')` on the sample is a nested AliasCode with `standardCode.code` rather than `type.code` directly. Cross-check the shape of a dateValues entry in the sample against the key-builder.

---

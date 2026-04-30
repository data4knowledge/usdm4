# USDM4 Engine Diff Report

Files seen: **234**, with alignment YAML: **234**, distinct rules observed: **214**.

## Bucket counts

| Bucket | Rules |
|---|---:|
| `d4k_under_reporting` | 7 |
| `d4k_over_reporting` | 14 |
| `aligned` | 192 |
| `core_only_rule` | 1 |

**Reading guide.**

- `d4k_under_reporting` — CORE finds errors d4k misses. **Treat each as a candidate d4k bug**, assuming the CORE finding is valid.
- `d4k_over_reporting` — d4k finds errors CORE doesn't. Either CORE is wrong (worth disputing upstream), or d4k is interpreting the rule more strictly than the spec intends.
- `mixed` — both kinds of disagreement appear across the corpus. Usually means the d4k implementation has both a missing case and an extra case.
- `d4k_exception` — d4k crashed on the rule. Investigate the stack trace before drawing conclusions.
- `d4k_not_impl` — the d4k rule is a stub. Implement it before treating it as a real comparison.
- `core_only_rule` — CORE-native rule with no DDF authority. d4k correctly has no counterpart; nothing to fix.

## d4k under-reporting — CORE finds errors d4k misses

### DDF00181  (under=231, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=3, total_files=234)

_CORE id(s)_: CORE-001068
**CORE description.** Date values associated to a study definition document version must be unique regarding the combination of type and geographic scopes of the date.

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0001` | Success(0) | Fail(2) | The study definition document version has more than one governance date with the same type and geographic scope. |
| `CORP0002` | Success(0) | Fail(2) | The study definition document version has more than one governance date with the same type and geographic scope. |
| `CORP0003` | Success(0) | Fail(2) | The study definition document version has more than one governance date with the same type and geographic scope. |
| `CORP0004` | Success(0) | Fail(2) | The study definition document version has more than one governance date with the same type and geographic scope. |
| `CORP0005` | Success(0) | Fail(2) | The study definition document version has more than one governance date with the same type and geographic scope. |

---

### DDF00093  (under=230, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=4, total_files=234)

_CORE id(s)_: CORE-000873
**DDF text.** Date values associated to a study version must be unique regarding the combination of type and geographic scopes of the date.

**CORE description.** Date values associated to a study version must be unique regarding the combination of type and geographic scopes of the date.

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0017` | Success(0) | Fail(2) | The study version has more than one governance date with the same type and geographic scope. |
| `CORP0001` | Failure(2) | Fail(3) | The study version has more than one governance date with the same type and geographic scope. |
| `CORP0002` | Failure(2) | Fail(3) | The study version has more than one governance date with the same type and geographic scope. |
| `CORP0003` | Failure(2) | Fail(3) | The study version has more than one governance date with the same type and geographic scope. |
| `CORP0004` | Failure(2) | Fail(3) | The study version has more than one governance date with the same type and geographic scope. |

---

### DDF00229  (under=222, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=12, total_files=234)

_CORE id(s)_: CORE-001058
**CORE description.** A study design's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0001` | Success(0) | Fail(1) | The study design's study phase is not specified according to the extensible Trial Phase Response (C66737) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive). |
| `CORP0002` | Success(0) | Fail(1) | The study design's study phase is not specified according to the extensible Trial Phase Response (C66737) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive). |
| `CORP0003` | Success(0) | Fail(1) | The study design's study phase is not specified according to the extensible Trial Phase Response (C66737) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive). |
| `CORP0004` | Success(0) | Fail(1) | The study design's study phase is not specified according to the extensible Trial Phase Response (C66737) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive). |
| `CORP0005` | Success(0) | Fail(1) | The study design's study phase is not specified according to the extensible Trial Phase Response (C66737) SDTM codelist - codeSystem is not "http://www.cdisc.org", codeSystemVersion is not a valid terminology package date, and/or the code or decode (either as preferred term or as submission value) is found in the codelist (case insensitive) but the corresponding decode or code does not match the codelist value (case sensitive). |

---

### DDF00010  (under=204, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=30, total_files=234)

_CORE id(s)_: CORE-001013
**CORE description.** The names of all instances of the same class must be unique.

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0001` | Success(0) | Fail(2) | The same name has been used for more than one instance of the class. |
| `CORP0002` | Success(0) | Fail(2) | The same name has been used for more than one instance of the class. |
| `CORP0003` | Success(0) | Fail(2) | The same name has been used for more than one instance of the class. |
| `CORP0004` | Success(0) | Fail(2) | The same name has been used for more than one instance of the class. |
| `CORP0005` | Success(0) | Fail(2) | The same name has been used for more than one instance of the class. |

---

### DDF00094  (under=204, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=30, total_files=234)

_CORE id(s)_: CORE-000814
**DDF text.** Within a study version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.

**CORE description.** Within a study version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0017` | Success(0) | Fail(2) | The study version has a type of governance date with a global geographic scope and either another date of the same type or additional geographic scope(s) defined for the date. |
| `CORP0001` | Failure(2) | Fail(3) | The study version has a type of governance date with a global geographic scope and either another date of the same type or additional geographic scope(s) defined for the date. |
| `CORP0002` | Failure(2) | Fail(3) | The study version has a type of governance date with a global geographic scope and either another date of the same type or additional geographic scope(s) defined for the date. |
| `CORP0003` | Failure(2) | Fail(3) | The study version has a type of governance date with a global geographic scope and either another date of the same type or additional geographic scope(s) defined for the date. |
| `CORP0004` | Failure(2) | Fail(3) | The study version has a type of governance date with a global geographic scope and either another date of the same type or additional geographic scope(s) defined for the date. |

---

### DDF00151  (under=204, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=30, total_files=234)

_CORE id(s)_: CORE-000834
**CORE description.** If geographic scope type is global then there must be only one geographic scope specified.

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0001` | Success(0) | Fail(2) | The governance date has more than one geographic scope defined, at least one of which has type of "Global" (type.code = C68846 or type.decode = "Global", both case insensitive). |
| `CORP0002` | Success(0) | Fail(2) | The governance date has more than one geographic scope defined, at least one of which has type of "Global" (type.code = C68846 or type.decode = "Global", both case insensitive). |
| `CORP0003` | Success(0) | Fail(2) | The governance date has more than one geographic scope defined, at least one of which has type of "Global" (type.code = C68846 or type.decode = "Global", both case insensitive). |
| `CORP0004` | Success(0) | Fail(2) | The governance date has more than one geographic scope defined, at least one of which has type of "Global" (type.code = C68846 or type.decode = "Global", both case insensitive). |
| `CORP0005` | Success(0) | Fail(2) | The governance date has more than one geographic scope defined, at least one of which has type of "Global" (type.code = C68846 or type.decode = "Global", both case insensitive). |

---

### DDF00025  (under=103, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=131, total_files=234)

_CORE id(s)_: CORE-000417
**CORE description.** A window must not be defined for an anchor timing (i.e., type is "Fixed Reference").

**Sample files where d4k under-reports:**

| file | d4k | core | core message |
|---|---:|---:|---|
| `CORP0013` | Success(0) | Fail(1) | One or more of the window attributes (windowLabel, windowLower, windowUpper) contains a value for a Fixed Reference timing (type.code=C201358). |
| `CORP0014` | Success(0) | Fail(1) | One or more of the window attributes (windowLabel, windowLower, windowUpper) contains a value for a Fixed Reference timing (type.code=C201358). |
| `CORP0015` | Success(0) | Fail(1) | One or more of the window attributes (windowLabel, windowLower, windowUpper) contains a value for a Fixed Reference timing (type.code=C201358). |
| `CORP0016` | Success(0) | Fail(1) | One or more of the window attributes (windowLabel, windowLower, windowUpper) contains a value for a Fixed Reference timing (type.code=C201358). |
| `CORP0018` | Success(0) | Fail(1) | One or more of the window attributes (windowLabel, windowLower, windowUpper) contains a value for a Fixed Reference timing (type.code=C201358). |

---

## d4k over-reporting — d4k finds errors CORE doesn't

### DDF00084  (under=0, over=234, exc=0, not_impl=0, aligned_fail=0, aligned_pass=0, total_files=234)

**DDF text.** Within a study design there must be exactly one objective with level 'Primary Objective'.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0001` | Failure(1) | Pass-or-NA(0) | Expected exactly one Primary Objective in study design, found 0 |
| `CORP0002` | Failure(1) | Pass-or-NA(0) | Expected exactly one Primary Objective in study design, found 0 |
| `CORP0003` | Failure(1) | Pass-or-NA(0) | Expected exactly one Primary Objective in study design, found 0 |
| `CORP0004` | Failure(1) | Pass-or-NA(0) | Expected exactly one Primary Objective in study design, found 0 |
| `CORP0005` | Failure(1) | Pass-or-NA(0) | Expected exactly one Primary Objective in study design, found 0 |

---

### DDF00155  (under=0, over=234, exc=0, not_impl=0, aligned_fail=0, aligned_pass=0, total_files=234)

**DDF text.** For CDISC codelist references (where the code system is 'http://www.cdisc.org'), the code system version must be a valid CDISC terminology release date in ISO 8601 date format.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `NCT04657016` | Failure(204) | Pass-or-NA(0) | Invalid codeSystemVersion |
| `NCT04660643` | Failure(189) | Pass-or-NA(0) | Invalid codeSystemVersion |
| `CORP0018` | Failure(187) | Pass-or-NA(0) | Invalid codeSystemVersion |
| `NCT05051579` | Failure(187) | Pass-or-NA(0) | Invalid codeSystemVersion |
| `NCT05134350` | Failure(178) | Pass-or-NA(0) | Invalid codeSystemVersion |

---

### DDF00166  (under=0, over=234, exc=0, not_impl=0, aligned_fail=0, aligned_pass=0, total_files=234)

**DDF text.** A study definition document type must be specified according to the extensible study definition document type (C215477) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0001` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Protocol', the decode is not in the codelist |
| `CORP0002` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Protocol', the decode is not in the codelist |
| `CORP0003` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Protocol', the decode is not in the codelist |
| `CORP0004` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Protocol', the decode is not in the codelist |
| `CORP0005` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Protocol', the decode is not in the codelist |

---

### DDF00227  (under=0, over=234, exc=0, not_impl=0, aligned_fail=0, aligned_pass=0, total_files=234)

**DDF text.** An interventional study must be specified using the InterventionalStudyDesign class.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0001` | Failure(1) | Pass-or-NA(0) | Required attribute 'studyType' is missing or empty |
| `CORP0002` | Failure(1) | Pass-or-NA(0) | Required attribute 'studyType' is missing or empty |
| `CORP0003` | Failure(1) | Pass-or-NA(0) | Required attribute 'studyType' is missing or empty |
| `CORP0004` | Failure(1) | Pass-or-NA(0) | Required attribute 'studyType' is missing or empty |
| `CORP0005` | Failure(1) | Pass-or-NA(0) | Required attribute 'studyType' is missing or empty |

---

### DDF00140  (under=0, over=227, exc=0, not_impl=0, aligned_fail=0, aligned_pass=7, total_files=234)

**DDF text.** An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0015` | Failure(6) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0016` | Failure(4) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0013` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0014` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `NCT02107703` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Clinical Study Registry', the decode is not in the codelist |

---

### DDF00200  (under=0, over=227, exc=0, not_impl=0, aligned_fail=0, aligned_pass=7, total_files=234)

**DDF text.** An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0015` | Failure(6) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0016` | Failure(4) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0013` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `CORP0014` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Pharmaceutical Company', the decode is not in the codelist |
| `NCT02107703` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Clinical Study Registry', the decode is not in the codelist |

---

### DDF00259  (under=0, over=227, exc=0, not_impl=0, aligned_fail=0, aligned_pass=7, total_files=234)

**DDF text.** A study role code must be specified according to the (C215480) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0015` | Failure(3) | Pass-or-NA(0) | Invalid decode 'Sponsor', the decode is not in the codelist |
| `CORP0016` | Failure(2) | Pass-or-NA(0) | Invalid decode 'Sponsor', the decode is not in the codelist |
| `CORP0001` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Sponsor', the decode is not in the codelist |
| `CORP0002` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Sponsor', the decode is not in the codelist |
| `CORP0003` | Failure(1) | Pass-or-NA(0) | Invalid decode 'Sponsor', the decode is not in the codelist |

---

### DDF00075  (under=0, over=216, exc=0, not_impl=0, aligned_fail=0, aligned_pass=18, total_files=234)

**DDF text.** An activity is expected to refer to at least one procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `NCT04677179` | Failure(157) | Pass-or-NA(0) | Activity does not reference any procedure, BC, BC category, or BC surrogate |
| `NCT04518410` | Failure(147) | Pass-or-NA(0) | Activity does not reference any procedure, BC, BC category, or BC surrogate |
| `NCT04666038` | Failure(116) | Pass-or-NA(0) | Activity does not reference any procedure, BC, BC category, or BC surrogate |
| `NCT06119529` | Failure(99) | Pass-or-NA(0) | Activity does not reference any procedure, BC, BC category, or BC surrogate |
| `NCT04145700` | Failure(95) | Pass-or-NA(0) | Activity does not reference any procedure, BC, BC category, or BC surrogate |

---

### DDF00031  (under=0, over=213, exc=0, not_impl=0, aligned_fail=0, aligned_pass=21, total_files=234)

**DDF text.** If timing type is not "Fixed Reference" then it must point to two scheduled instances (e.g. the relativeFromScheduledInstance and relativeToScheduledInstance attributes must not be missing and must not be equal to each other).

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0002` | Failure(1) | Pass-or-NA(0) | relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal |
| `CORP0003` | Failure(1) | Pass-or-NA(0) | relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal |
| `CORP0004` | Failure(1) | Pass-or-NA(0) | relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal |
| `CORP0005` | Failure(1) | Pass-or-NA(0) | relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal |
| `CORP0007` | Failure(1) | Pass-or-NA(0) | relativeToScheduledInstanceId and relativeFromScheduledInstanceId are equal |

---

### DDF00087  (under=0, over=210, exc=0, not_impl=0, aligned_fail=0, aligned_pass=24, total_files=234)

**DDF text.** Encounter ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0002` | Failure(2) | Pass-or-NA(0) | StudyDesign has 18 encounter chain heads (previousId=null) — expected 1 |
| `CORP0003` | Failure(2) | Pass-or-NA(0) | StudyDesign has 17 encounter chain heads (previousId=null) — expected 1 |
| `CORP0004` | Failure(2) | Pass-or-NA(0) | StudyDesign has 15 encounter chain heads (previousId=null) — expected 1 |
| `CORP0007` | Failure(2) | Pass-or-NA(0) | StudyDesign has 15 encounter chain heads (previousId=null) — expected 1 |
| `CORP0011` | Failure(2) | Pass-or-NA(0) | StudyDesign has 16 encounter chain heads (previousId=null) — expected 1 |

---

### DDF00110  (under=0, over=200, exc=0, not_impl=0, aligned_fail=0, aligned_pass=34, total_files=234)

**DDF text.** An eligibility criterion's category must be specified using the Category of Inclusion/Exclusion (C66797) SDTM codelist.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `NCT02291289` | Failure(101) | Pass-or-NA(0) | Invalid decode 'INCLUSION', the decode is not in the codelist |
| `NCT05051579` | Failure(68) | Pass-or-NA(0) | Invalid decode 'INCLUSION', the decode is not in the codelist |
| `NCT04730349` | Failure(61) | Pass-or-NA(0) | Invalid decode 'INCLUSION', the decode is not in the codelist |
| `NCT05855967` | Failure(61) | Pass-or-NA(0) | Invalid decode 'INCLUSION', the decode is not in the codelist |
| `NCT03637764` | Failure(60) | Pass-or-NA(0) | Invalid decode 'INCLUSION', the decode is not in the codelist |

---

### DDF00249  (under=0, over=200, exc=0, not_impl=0, aligned_fail=0, aligned_pass=34, total_files=234)

**DDF text.** An eligibility criterion item is expected to be used in at least one study design.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `NCT02291289` | Failure(101) | Pass-or-NA(0) | Required attribute 'criterionItem' is missing or empty |
| `NCT05051579` | Failure(68) | Pass-or-NA(0) | Required attribute 'criterionItem' is missing or empty |
| `NCT04730349` | Failure(61) | Pass-or-NA(0) | Required attribute 'criterionItem' is missing or empty |
| `NCT05855967` | Failure(61) | Pass-or-NA(0) | Required attribute 'criterionItem' is missing or empty |
| `NCT03637764` | Failure(60) | Pass-or-NA(0) | Required attribute 'criterionItem' is missing or empty |

---

### DDF00088  (under=0, over=177, exc=0, not_impl=0, aligned_fail=0, aligned_pass=57, total_files=234)

_CORE id(s)_: CORE-001048
**DDF text.** Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

**CORE description.** Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0003` | Failure(2) | Pass-or-NA(0) | StudyDesign has 3 epoch chain heads (previousId=null) — expected 1 |
| `CORP0007` | Failure(2) | Pass-or-NA(0) | StudyDesign has 3 epoch chain heads (previousId=null) — expected 1 |
| `CORP0011` | Failure(2) | Pass-or-NA(0) | StudyDesign has 3 epoch chain heads (previousId=null) — expected 1 |
| `CORP0013` | Failure(2) | Pass-or-NA(0) | StudyDesign has 2 epoch chain heads (previousId=null) — expected 1 |
| `CORP0014` | Failure(2) | Pass-or-NA(0) | StudyDesign has 2 epoch chain heads (previousId=null) — expected 1 |

---

### DDF00045  (under=0, over=25, exc=0, not_impl=0, aligned_fail=0, aligned_pass=209, total_files=234)

**DDF text.** At least one attribute must be specified for an address.

**Sample files where d4k over-reports:**

| file | d4k | core | d4k message |
|---|---:|---:|---|
| `CORP0015` | Failure(3) | Pass-or-NA(0) | No attributes specified for address |
| `CORP0012` | Failure(1) | Pass-or-NA(0) | No attributes specified for address |
| `CORP0014` | Failure(1) | Pass-or-NA(0) | No attributes specified for address |
| `CORP0016` | Failure(1) | Pass-or-NA(0) | No attributes specified for address |
| `NCT02107703` | Failure(1) | Pass-or-NA(0) | No attributes specified for address |

---

## Aligned (no divergence on any file)

### DDF00006  (under=0, over=0, exc=0, not_impl=0, aligned_fail=105, aligned_pass=129, total_files=234)

_CORE id(s)_: CORE-000402
**DDF text.** Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.

**CORE description.** Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.

---

### DDF00007  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00008  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00009  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00011  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00012  (under=0, over=0, exc=0, not_impl=0, aligned_fail=21, aligned_pass=213, total_files=234)

_CORE id(s)_: CORE-000407
**DDF text.** Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

**CORE description.** Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

---

### DDF00013  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00014  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00017  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00018  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00019  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00020  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00021  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00022  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00023  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00024  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00026  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00027  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00028  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00029  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00030  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00032  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00033  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00034  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00035  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00036  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00037  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00038  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00039  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00040  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00041  (under=0, over=0, exc=0, not_impl=0, aligned_fail=234, aligned_pass=0, total_files=234)

_CORE id(s)_: CORE-001036
**DDF text.** Within a study design, there must be at least one endpoint with level primary.

**CORE description.** Within a study design, there must be at least one endpoint with level primary.

---

### DDF00042  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00044  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00046  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00047  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00050  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00051  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00052  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00054  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00058  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00059  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00060  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00061  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00062  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00063  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00069  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00071  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00072  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00073  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00076  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00080  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00081  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00082  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00083  (under=0, over=0, exc=0, not_impl=0, aligned_fail=204, aligned_pass=30, total_files=234)

_CORE id(s)_: CORE-001015
**DDF text.** Within a study version, all id values must be unique.

**CORE description.** Within a study version, all id values must be unique.

---

### DDF00090  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00091  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00096  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00097  (under=0, over=0, exc=0, not_impl=0, aligned_fail=234, aligned_pass=0, total_files=234)

_CORE id(s)_: CORE-000815
**DDF text.** Within a study design, the planned age range must be specified either in the study population or in all cohorts.

**CORE description.** Within a study design, the planned age range must be specified either in the study population or in all cohorts.

---

### DDF00098  (under=0, over=0, exc=0, not_impl=0, aligned_fail=234, aligned_pass=0, total_files=234)

_CORE id(s)_: CORE-000875
**DDF text.** Within a study design, the planned sex must be specified either in the study population or in all cohorts.

**CORE description.** Within a study design, the planned sex must be specified either in the study population or in all cohorts.

---

### DDF00099  (under=0, over=0, exc=0, not_impl=0, aligned_fail=1, aligned_pass=233, total_files=234)

_CORE id(s)_: CORE-000816
**DDF text.** All epochs are expected to be referred to from a scheduled Activity Instance.

**CORE description.** All epochs are expected to be referred to from a scheduled Activity Instance.

---

### DDF00100  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00101  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00102  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00104  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00105  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00106  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00107  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00108  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00112  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00114  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00115  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00124  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00125  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00126  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00127  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00128  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00132  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00133  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00136  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00137  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00141  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00142  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00143  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00144  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00146  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00147  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00148  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00149  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00150  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00152  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00153  (under=0, over=0, exc=0, not_impl=0, aligned_fail=213, aligned_pass=21, total_files=234)

_CORE id(s)_: CORE-001016
**DDF text.** A planned duration is expected for the main timeline.

**CORE description.** A planned duration is expected for the main timeline.

---

### DDF00154  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00156  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00157  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00158  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00159  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00160  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00161  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00162  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00163  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00164  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00165  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00167  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00168  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00169  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00170  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00171  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00172  (under=0, over=0, exc=0, not_impl=0, aligned_fail=7, aligned_pass=227, total_files=234)

_CORE id(s)_: CORE-001054
**DDF text.** There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).

**CORE description.** There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).

---

### DDF00173  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00174  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00175  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00176  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00177  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00178  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00179  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00180  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00182  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00183  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00184  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00185  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00186  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00187  (under=0, over=0, exc=0, not_impl=0, aligned_fail=156, aligned_pass=78, total_files=234)

_CORE id(s)_: CORE-001069
**DDF text.** Narrative content item text is expected to be HTML formatted.

**CORE description.** Narrative content item text is expected to be HTML formatted.

---

### DDF00188  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00189  (under=0, over=0, exc=0, not_impl=0, aligned_fail=227, aligned_pass=7, total_files=234)

_CORE id(s)_: CORE-000970
**DDF text.** Every study role must apply to either a study version or at least one study design, but not both.

**CORE description.** Every study role must apply to either a study version or at least one study design, but not both.

---

### DDF00190  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00191  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00192  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00193  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00194  (under=0, over=0, exc=0, not_impl=0, aligned_fail=25, aligned_pass=209, total_files=234)

_CORE id(s)_: CORE-000971
**DDF text.** At least one attribute must be specified for an address.

**CORE description.** At least one attribute must be specified for an address.

---

### DDF00195  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00196  (under=0, over=0, exc=0, not_impl=0, aligned_fail=6, aligned_pass=228, total_files=234)

_CORE id(s)_: CORE-000985
**DDF text.** There must be a one-to-one relationship between referenced section number and title within a study amendment.

**CORE description.** There must be a one-to-one relationship between referenced section number and title within any study definition document affected by a study amendment.

---

### DDF00197  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00198  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00199  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00201  (under=0, over=0, exc=0, not_impl=0, aligned_fail=7, aligned_pass=227, total_files=234)

_CORE id(s)_: CORE-000973
**DDF text.** There must be exactly one study role with a code of sponsor.

**CORE description.** There must be exactly one study role with a code of sponsor.

---

### DDF00202  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00203  (under=0, over=0, exc=0, not_impl=0, aligned_fail=227, aligned_pass=7, total_files=234)

_CORE id(s)_: CORE-000974
**DDF text.** The sponsor study role must be applicable to a study version.

**CORE description.** The sponsor study role must be applicable to a study version.

---

### DDF00204  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00205  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00206  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00207  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00208  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00209  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00210  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00211  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00212  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00213  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00214  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00215  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00216  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00217  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00218  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00219  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00220  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00221  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00222  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00223  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00224  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00225  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00226  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00228  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00230  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00231  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00232  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00233  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00234  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00235  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00236  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00237  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00238  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00239  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00240  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00241  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00242  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00243  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00244  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00245  (under=0, over=0, exc=0, not_impl=0, aligned_fail=114, aligned_pass=120, total_files=234)

_CORE id(s)_: CORE-001041
**DDF text.** Within a document version, the specified section numbers for narrative content must be unique.

**CORE description.** Within a document version, the specified displayed section numbers for narrative content must be unique.

---

### DDF00246  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00247  (under=0, over=0, exc=0, not_impl=0, aligned_fail=14, aligned_pass=220, total_files=234)

_CORE id(s)_: CORE-000945
**DDF text.** Syntax template text is expected to be HTML formatted.

**CORE description.** Syntax template text is expected to be HTML formatted.

---

### DDF00248  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00250  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00251  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00252  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00253  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00254  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00255  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00256  (under=0, over=0, exc=0, not_impl=0, aligned_fail=8, aligned_pass=226, total_files=234)

_CORE id(s)_: CORE-001031
**DDF text.** The same reason is not expected to be given as a primary and secondary reason.

**CORE description.** The same reason is not expected to be given as a primary and secondary reason.

---

### DDF00257  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00258  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00260  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDF00261  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

### DDFSDW001  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=234, total_files=234)

---

## CORE-only rules (no DDF mapping)

### DDF00263  (under=0, over=0, exc=0, not_impl=0, aligned_fail=0, aligned_pass=0, total_files=216)

_CORE id(s)_: CORE-001076
**CORE description.** An activity is expected to refer to at least one procedure, biomedical concept, biomedical concept category, biomedical concept surrogate, child activity, or timeline.

---

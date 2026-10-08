# d4k Extension Identifiers

CS_EXT_URL = "www.d4k.dk/usdm/extensions/001"  # Confidentiality statement
OV_EXT_URL = "www.d4k.dk/usdm/extensions/002"  # Original protocol (original version)
SI_EXT_URL = (
    "www.d4k.dk/usdm/extensions/003"  # Site identifier scope. An array of extensions.
)
CC_EXT_URL = "www.d4k.dk/usdm/extensions/004"  # Compund codes
CN_EXT_URL = "www.d4k.dk/usdm/extensions/005"  # Compund names
MECDL_EXT_URL = (
    "www.d4k.dk/usdm/extensions/006"  # Medical expert contact details location
)
SS_EXT_URL = "www.d4k.dk/usdm/extensions/007"  # Sponsor signatory
SAL_EXT_URL = "www.d4k.dk/usdm/extensions/008"  # Sponsor approval info location
SIT_EXT_URL = "www.d4k.dk/usdm/extensions/009"  # Study identifier type
APCD_EXT_URL = "www.d4k.dk/usdm/extensions/010"  # Assigned person contact details

# Timeline classification, set when the SoA input carries one. A sampling or
# dosing profile is a standalone timeline timed relative to a dose or a meal
# rather than to the study calendar, and what kind of table it was read from is
# worth keeping: a consumer sophisticated enough to connect a profile into the
# main timeline needs to know which timelines are profiles, which way round the
# source table ran, and in what unit.
#
# One concept per URL, matching every extension above. These four are emitted
# together or not at all, so the presence of TLF is what marks a timeline as a
# profile — its values name profile families.
TLF_EXT_URL = "www.d4k.dk/usdm/extensions/011"  # Timeline source family
TLO_EXT_URL = "www.d4k.dk/usdm/extensions/012"  # Timeline source orientation
TLU_EXT_URL = "www.d4k.dk/usdm/extensions/013"  # Timeline timing-axis unit
TLP_EXT_URL = "www.d4k.dk/usdm/extensions/014"  # Timeline source placement

# Intervention model provenance, set when the assembler had to DEFAULT the study
# design's ``model`` rather than encode a value the caller supplied. ``model`` is
# required on InterventionalStudyDesign and validated against C99076, so a design
# whose model was never stated still carries a real term from that codelist.
# Without this attribute nothing on the output distinguishes that term from one
# the caller asserted. Absent on every design whose model was decoded, which is
# what every design carried before.
IMP_EXT_URL = "www.d4k.dk/usdm/extensions/015"  # Intervention model provenance

# Timeline type: the input's ``ScheduleTimelineInput.type`` (``main``,
# ``follow_up``, ``profile``, ...), written on every built ScheduleTimeline.
# For debugging and for assessing how well callers type their timelines.
# Nothing in the build reads it; TLF still marks profiles.
TLT_EXT_URL = "www.d4k.dk/usdm/extensions/016"  # Timeline type

# Epoch provenance, set on the one epoch the study design assembler SYNTHESISES
# when arms name interventions and no epoch exists. USDM links an arm to its
# interventions only through a study cell, and a cell needs an epoch, so without
# it the link is lost. The epoch is typed Treatment Epoch like every epoch the
# timeline build makes, so this attribute is the only thing that separates it
# from a stated one. Anything that exports epochs must skip an epoch carrying it.
EPP_EXT_URL = "www.d4k.dk/usdm/extensions/017"  # Epoch provenance

# M11 1.1.2 Control Type (codelist C217279), at most one attribute (M11
# cardinality One to one), valueCode. USDM has no home for it: StudyDesign.characteristics is
# bound to C207416, which holds none of these terms, and arm types cannot
# express Dose Response, Different Dose or Regimen or External (GitHub 86).
CT_EXT_URL = "www.d4k.dk/usdm/extensions/018"  # Control type

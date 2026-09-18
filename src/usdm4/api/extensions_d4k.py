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

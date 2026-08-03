"""Guard: every concrete API model class must appear in usdm4.api.__all__.

__all__ seeds the Builder's IdManager id index; a class missing from it
makes builder.create fail with KeyError for that class. This has now
happened three times (MedicalDevice/Substance/ProductOrganizationRole,
then CommentAnnotation, BiospecimenRetention and ConditionAssignment) —
this test makes the next omission a test failure, not a runtime crash.
"""

import re
import glob
import os

import usdm4.api as api

# Base / abstract classes never instantiated via the builder.
NON_CONCRETE = {
    "ApiBaseModel",
    "ApiBaseModelWithId",
    "ApiBaseModelWithIdOnly",
    "ApiBaseModelWithIdAndDesc",
    "ApiBaseModelWithIdAndName",
    "ApiBaseModelWithIdNameAndDesc",
    "ApiBaseModelWithIdNameAndLabel",
    "ApiBaseModelWithIdNameLabelAndDesc",
    "BaseAliasCode",
    "BaseCode",
    "BaseDataType",
    "BaseQuantity",
    "BaseRange",
    "Extension",
    "Identifier",
    "PopulationDefinition",
    "QuantityRange",
}


def test_all_covers_every_concrete_api_class():
    api_dir = os.path.dirname(api.__file__)
    defined = set()
    for path in glob.glob(os.path.join(api_dir, "*.py")):
        if os.path.basename(path) == "__init__.py":
            continue
        with open(path) as f:
            defined.update(re.findall(r"^class (\w+)\(", f.read(), re.M))
    missing = sorted(defined - NON_CONCRETE - set(api.__all__))
    assert missing == [], (
        f"Concrete API classes missing from usdm4.api.__all__ (builder "
        f"creation would fail with KeyError): {missing}"
    )

"""Tests for the usdm4.api package exports (__all__)."""

import src.usdm4.api as api


def test_all_has_no_duplicates():
    assert len(api.__all__) == len(set(api.__all__)), (
        f"Duplicates in __all__: "
        f"{[n for n in set(api.__all__) if api.__all__.count(n) > 1]}"
    )


def test_all_names_are_importable():
    for name in api.__all__:
        assert hasattr(api, name), f"'{name}' in __all__ but not importable"


def test_medical_device_and_product_organization_role_exported():
    # Previously missing from __all__, so IdManager had no index entry and
    # builder.create() raised KeyError for these classes.
    assert "MedicalDevice" in api.__all__
    assert "ProductOrganizationRole" in api.__all__

from src.usdm4.api.api_base_model import ApiBaseModelWithIdNameAndLabel


def test_label():
    instance_1 = ApiBaseModelWithIdNameAndLabel(id="dummy", name="NAME", label="LABEL")
    instance_2 = ApiBaseModelWithIdNameAndLabel(id="dummy", name="NAME", label="")
    assert instance_1.label_name() == "LABEL"
    assert instance_2.label_name() == "NAME"

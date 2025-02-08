from usdm4.rules.rules_validation import RuleValidation

__package_name__ = "USDM4"
__package_version__ = "0.1.0"
__model_version__ = "3.6.0"

def validate(data: dict) -> bool:
    """
    Validate the data against the USDM4 model.
    """
    return RuleValidation.validate(data)


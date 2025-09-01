from src.usdm4.rules.rules_validation import RulesValidation


def clear_rules_library():
    type(RulesValidation)._clear(RulesValidation)

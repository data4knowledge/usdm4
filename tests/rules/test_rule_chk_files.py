import pytest
from unittest.mock import Mock

# Import all rule_chk classes
from src.usdm4.rules.library.rule_chk0004 import RuleCHK0004
from src.usdm4.rules.library.rule_chk0050 import RuleCHK0050
from src.usdm4.rules.library.rule_chk0061 import RuleCHK0061
from src.usdm4.rules.library.rule_chk0062 import RuleCHK0062
from src.usdm4.rules.library.rule_chk0063 import RuleCHK0063
from src.usdm4.rules.library.rule_chk0064 import RuleCHK0064
from src.usdm4.rules.library.rule_chk0120 import RuleCHK0120
from src.usdm4.rules.library.rule_chk0167 import RuleCHK0167
from src.usdm4.rules.library.rule_chk0170 import RuleCHK0170
from src.usdm4.rules.library.rule_chk0171 import RuleCHK0171
from src.usdm4.rules.library.rule_chk0173 import RuleCHK0173
from src.usdm4.rules.library.rule_chk0174 import RuleCHK0174
from src.usdm4.rules.library.rule_chk0178 import RuleCHK0178
from src.usdm4.rules.library.rule_chk0179 import RuleCHK0179
from src.usdm4.rules.library.rule_chk0181 import RuleCHK0181
from src.usdm4.rules.library.rule_chk0182 import RuleCHK0182
from src.usdm4.rules.library.rule_chk0183 import RuleCHK0183
from src.usdm4.rules.library.rule_chk0184 import RuleCHK0184
from src.usdm4.rules.library.rule_chk0185 import RuleCHK0185
from src.usdm4.rules.library.rule_chk0187 import RuleCHK0187
from src.usdm4.rules.library.rule_chk0188 import RuleCHK0188
from src.usdm4.rules.library.rule_chk0189 import RuleCHK0189
from src.usdm4.rules.library.rule_chk0191 import RuleCHK0191
from src.usdm4.rules.library.rule_chk0192 import RuleCHK0192
from src.usdm4.rules.library.rule_chk0193 import RuleCHK0193
from src.usdm4.rules.library.rule_chk0195 import RuleCHK0195
from src.usdm4.rules.library.rule_chk0197 import RuleCHK0197
from src.usdm4.rules.library.rule_chk0199 import RuleCHK0199
from src.usdm4.rules.library.rule_chk0200 import RuleCHK0200
from src.usdm4.rules.library.rule_chk0201 import RuleCHK0201
from src.usdm4.rules.library.rule_chk0202 import RuleCHK0202
from src.usdm4.rules.library.rule_chk0203 import RuleCHK0203
from src.usdm4.rules.library.rule_chk0204 import RuleCHK0204
from src.usdm4.rules.library.rule_chk0207 import RuleCHK0207
from src.usdm4.rules.library.rule_chk0208 import RuleCHK0208
from src.usdm4.rules.library.rule_chk0214 import RuleCHK0214
from src.usdm4.rules.library.rule_chk0219 import RuleCHK0219
from src.usdm4.rules.library.rule_chk0220 import RuleCHK0220
from src.usdm4.rules.library.rule_chk0221 import RuleCHK0221
from src.usdm4.rules.library.rule_chk0231 import RuleCHK0231
from src.usdm4.rules.library.rule_chk0232 import RuleCHK0232
from src.usdm4.rules.library.rule_chk0233 import RuleCHK0233
from src.usdm4.rules.library.rule_chk0234 import RuleCHK0234
from src.usdm4.rules.library.rule_chk0235 import RuleCHK0235
from src.usdm4.rules.library.rule_chk0236 import RuleCHK0236
from src.usdm4.rules.library.rule_chk0237 import RuleCHK0237
from src.usdm4.rules.library.rule_chk0238 import RuleCHK0238
from src.usdm4.rules.library.rule_chk0239 import RuleCHK0239
from src.usdm4.rules.library.rule_chk0240 import RuleCHK0240
from src.usdm4.rules.library.rule_chk0241 import RuleCHK0241
from src.usdm4.rules.library.rule_chk0242 import RuleCHK0242
from src.usdm4.rules.library.rule_chk0243 import RuleCHK0243
from src.usdm4.rules.library.rule_chk0244 import RuleCHK0244
from src.usdm4.rules.library.rule_chk0245 import RuleCHK0245
from src.usdm4.rules.library.rule_chk0246 import RuleCHK0246
from src.usdm4.rules.library.rule_chk0247 import RuleCHK0247
from src.usdm4.rules.library.rule_chk0248 import RuleCHK0248
from src.usdm4.rules.library.rule_chk0249 import RuleCHK0249
from src.usdm4.rules.library.rule_chk0250 import RuleCHK0250
from src.usdm4.rules.library.rule_chk0251 import RuleCHK0251
from src.usdm4.rules.library.rule_chk0252 import RuleCHK0252
from src.usdm4.rules.library.rule_chk0253 import RuleCHK0253
from src.usdm4.rules.library.rule_chk0254 import RuleCHK0254
from src.usdm4.rules.library.rule_chk0255 import RuleCHK0255
from src.usdm4.rules.library.rule_chk0256 import RuleCHK0256
from src.usdm4.rules.library.rule_chk0257 import RuleCHK0257
from src.usdm4.rules.library.rule_chk0258 import RuleCHK0258
from src.usdm4.rules.library.rule_chk0259 import RuleCHK0259
from src.usdm4.rules.library.rule_chk0260 import RuleCHK0260
from src.usdm4.rules.library.rule_chk0261 import RuleCHK0261
from src.usdm4.rules.library.rule_chk0262 import RuleCHK0262
from src.usdm4.rules.library.rule_chk0263 import RuleCHK0263
from src.usdm4.rules.library.rule_chk0264 import RuleCHK0264
from src.usdm4.rules.library.rule_chk0265 import RuleCHK0265
from src.usdm4.rules.library.rule_chk0266 import RuleCHK0266
from src.usdm4.rules.library.rule_chk0267 import RuleCHK0267
from src.usdm4.rules.library.rule_chk0268 import RuleCHK0268
from src.usdm4.rules.library.rule_chk0269 import RuleCHK0269
from src.usdm4.rules.library.rule_chk0270 import RuleCHK0270
from src.usdm4.rules.library.rule_chk0271 import RuleCHK0271
from src.usdm4.rules.library.rule_chk0272 import RuleCHK0272
from src.usdm4.rules.library.rule_chk0273 import RuleCHK0273
from src.usdm4.rules.library.rule_chk0274 import RuleCHK0274
from src.usdm4.rules.library.rule_chk0275 import RuleCHK0275
from src.usdm4.rules.library.rule_chk0276 import RuleCHK0276


class TestRuleCHKFiles:
    """Test all rule_chk files that follow the pattern rule_chk followed by four digits."""
    
    # List of all rule classes and their expected rule IDs
    RULE_CLASSES = [
        (RuleCHK0004, "CHK0004"),
        (RuleCHK0050, "CHK0050"),
        (RuleCHK0061, "CHK0061"),
        (RuleCHK0062, "CHK0062"),
        (RuleCHK0063, "CHK0063"),
        (RuleCHK0064, "CHK0064"),
        (RuleCHK0120, "CHK0120"),
        (RuleCHK0167, "CHK0167"),
        (RuleCHK0170, "CHK0170"),
        (RuleCHK0171, "CHK0171"),
        (RuleCHK0173, "CHK0173"),
        (RuleCHK0174, "CHK0174"),
        (RuleCHK0178, "CHK0178"),
        (RuleCHK0179, "CHK0179"),
        (RuleCHK0181, "CHK0181"),
        (RuleCHK0182, "CHK0182"),
        (RuleCHK0183, "CHK0183"),
        (RuleCHK0184, "CHK0184"),
        (RuleCHK0185, "CHK0185"),
        (RuleCHK0187, "CHK0187"),
        (RuleCHK0188, "CHK0188"),
        (RuleCHK0189, "CHK0189"),
        (RuleCHK0191, "CHK0191"),
        (RuleCHK0192, "CHK0192"),
        (RuleCHK0193, "CHK0193"),
        (RuleCHK0195, "CHK0195"),
        (RuleCHK0197, "CHK0197"),
        (RuleCHK0199, "CHK0199"),
        (RuleCHK0200, "CHK0200"),
        (RuleCHK0201, "CHK0201"),
        (RuleCHK0202, "CHK0202"),
        (RuleCHK0203, "CHK0203"),
        (RuleCHK0204, "CHK0204"),
        (RuleCHK0207, "CHK0207"),
        (RuleCHK0208, "CHK0208"),
        (RuleCHK0214, "CHK0214"),
        (RuleCHK0219, "CHK0219"),
        (RuleCHK0220, "CHK0220"),
        (RuleCHK0221, "CHK0221"),
        (RuleCHK0231, "CHK0231"),
        (RuleCHK0232, "CHK0232"),
        (RuleCHK0233, "CHK0233"),
        (RuleCHK0234, "CHK0234"),
        (RuleCHK0235, "CHK0235"),
        (RuleCHK0236, "CHK0236"),
        (RuleCHK0237, "CHK0237"),
        (RuleCHK0238, "CHK0238"),
        (RuleCHK0239, "CHK0239"),
        (RuleCHK0240, "CHK0240"),
        (RuleCHK0241, "CHK0241"),
        (RuleCHK0242, "CHK0242"),
        (RuleCHK0243, "CHK0243"),
        (RuleCHK0244, "CHK0244"),
        (RuleCHK0245, "CHK0245"),
        (RuleCHK0246, "CHK0246"),
        (RuleCHK0247, "CHK0247"),
        (RuleCHK0248, "CHK0248"),
        (RuleCHK0249, "CHK0249"),
        (RuleCHK0250, "CHK0250"),
        (RuleCHK0251, "CHK0251"),
        (RuleCHK0252, "CHK0252"),
        (RuleCHK0253, "CHK0253"),
        (RuleCHK0254, "CHK0254"),
        (RuleCHK0255, "CHK0255"),
        (RuleCHK0256, "CHK0256"),
        (RuleCHK0257, "CHK0257"),
        (RuleCHK0258, "CHK0258"),
        (RuleCHK0259, "CHK0259"),
        (RuleCHK0260, "CHK0260"),
        (RuleCHK0261, "CHK0261"),
        (RuleCHK0262, "CHK0262"),
        (RuleCHK0263, "CHK0263"),
        (RuleCHK0264, "CHK0264"),
        (RuleCHK0265, "CHK0265"),
        (RuleCHK0266, "CHK0266"),
        (RuleCHK0267, "CHK0267"),
        (RuleCHK0268, "CHK0268"),
        (RuleCHK0269, "CHK0269"),
        (RuleCHK0270, "CHK0270"),
        (RuleCHK0271, "CHK0271"),
        (RuleCHK0272, "CHK0272"),
        (RuleCHK0273, "CHK0273"),
        (RuleCHK0274, "CHK0274"),
        (RuleCHK0275, "CHK0275"),
        (RuleCHK0276, "CHK0276"),
    ]

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_initialization(self, rule_class, expected_rule_id):
        """Test that each rule class can be instantiated properly."""
        rule = rule_class()
        assert rule is not None
        assert hasattr(rule, 'validate')
        assert callable(rule.validate)

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_validate_raises_not_implemented_error(self, rule_class, expected_rule_id):
        """Test that each rule's validate method raises NotImplementedError."""
        rule = rule_class()
        config = {"test": "config"}
        
        with pytest.raises(NotImplementedError) as exc_info:
            rule.validate(config)
        
        assert str(exc_info.value) == "rule is not implemented"

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_validate_with_empty_config(self, rule_class, expected_rule_id):
        """Test that each rule's validate method raises NotImplementedError even with empty config."""
        rule = rule_class()
        config = {}
        
        with pytest.raises(NotImplementedError) as exc_info:
            rule.validate(config)
        
        assert str(exc_info.value) == "rule is not implemented"

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_validate_with_none_config(self, rule_class, expected_rule_id):
        """Test that each rule's validate method raises NotImplementedError even with None config."""
        rule = rule_class()
        
        with pytest.raises(NotImplementedError) as exc_info:
            rule.validate(None)
        
        assert str(exc_info.value) == "rule is not implemented"

    def test_all_rules_count(self):
        """Test that we have the expected number of rule classes."""
        assert len(self.RULE_CLASSES) == 85, f"Expected 85 rule classes, but found {len(self.RULE_CLASSES)}"

    def test_rule_ids_are_unique(self):
        """Test that all rule IDs are unique."""
        rule_ids = [rule_id for _, rule_id in self.RULE_CLASSES]
        assert len(rule_ids) == len(set(rule_ids)), "Rule IDs should be unique"

    def test_rule_classes_are_unique(self):
        """Test that all rule classes are unique."""
        rule_classes = [rule_class for rule_class, _ in self.RULE_CLASSES]
        assert len(rule_classes) == len(set(rule_classes)), "Rule classes should be unique"

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_class_name_matches_expected_pattern(self, rule_class, expected_rule_id):
        """Test that each rule class name matches the expected pattern."""
        class_name = rule_class.__name__
        expected_class_name = f"Rule{expected_rule_id}"
        assert class_name == expected_class_name, f"Expected class name {expected_class_name}, got {class_name}"

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_has_docstring(self, rule_class, expected_rule_id):
        """Test that each rule class has a docstring."""
        assert rule_class.__doc__ is not None, f"Rule {expected_rule_id} should have a docstring"
        assert len(rule_class.__doc__.strip()) > 0, f"Rule {expected_rule_id} docstring should not be empty"

    @pytest.mark.parametrize("rule_class,expected_rule_id", RULE_CLASSES)
    def test_rule_docstring_contains_rule_id(self, rule_class, expected_rule_id):
        """Test that each rule's docstring contains the rule ID."""
        docstring = rule_class.__doc__
        assert expected_rule_id in docstring, f"Rule {expected_rule_id} docstring should contain the rule ID"

    def test_rule_instantiation_performance(self):
        """Test that all rules can be instantiated quickly."""
        import time
        start_time = time.time()
        
        for rule_class, _ in self.RULE_CLASSES:
            rule = rule_class()
            assert rule is not None
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Should be able to instantiate all 85 rules in less than 1 second
        assert elapsed_time < 1.0, f"Rule instantiation took too long: {elapsed_time:.3f} seconds"

    def test_rule_validate_method_signature(self):
        """Test that all rules have the correct validate method signature."""
        for rule_class, _ in self.RULE_CLASSES:
            rule = rule_class()
            validate_method = getattr(rule, 'validate')
            
            # Check that the method exists and is callable
            assert callable(validate_method), f"validate method should be callable for {rule_class.__name__}"
            
            # Check method signature by trying to call it with a config parameter
            try:
                validate_method({})
            except NotImplementedError:
                # This is expected
                pass
            except TypeError as e:
                pytest.fail(f"validate method signature is incorrect for {rule_class.__name__}: {e}")

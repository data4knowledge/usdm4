import json
from pathlib import Path
import re


class RuleGenerator:
    def __init__(self, json_path: str, output_dir: str):
        """
        Initialize the rule generator

        Args:
            json_path (str): Path to the JSON rules file
            output_dir (str): Directory where rule files will be created
        """
        self.json_path = Path(json_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_text(self, text: str) -> str:
        """Clean text for use in Python docstrings"""
        return text.replace('"', '\\"').replace("\\/", "/")

    def _create_class_name(self, rule_id: str) -> str:
        """Generate a class name from the rule ID"""
        # Remove 'DDF' prefix and convert to CamelCase
        name = rule_id.replace("DDF", "")
        return f"Rule{name}"

    def generate_rule_file(self, rule: dict) -> None:
        """Generate a single rule file from a rule dictionary"""
        rule_id = rule.get("Final CORE Rule ID")
        if not rule_id:
            return

        # Create file path
        file_path = self.output_dir / f"rule_{rule_id.lower()}.py"

        # Determine reporting level
        level = (
            "WARNING"
            if "WARNING" in rule.get("Warning/ Error", "").upper()
            else "ERROR"
        )

        # Create file content
        content = f'''from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation

class {self._create_class_name(rule_id)}(RuleTemplate):
    """
    {rule_id}: {self._sanitize_text(rule["Textual statement of rule"])}
    
    Applies to: {rule["Entity(ies) to which the rule applies"]}
    Attributes: {rule["Attributes within the entity(ies) to which the rule applies"]}
    """
    
    def __init__(self):
        super().__init__("{rule_id}", RuleTemplate.{level}, "{self._sanitize_text(rule["Textual statement of rule"])}")
    
    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data
        
        Args:
            config (dict): Standard configuration structure contain the data, CT etc
            
        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
'''

        # Write the file
        with open(file_path, "w") as f:
            f.write(content)

    def generate_all_rules(self):
        """Generate all rule files from the JSON specification"""
        with open(self.json_path) as f:
            data = json.load(f)

        # Get the rules array (assuming it's the first key in the JSON)
        rules = data[list(data.keys())[0]]

        for rule in rules:
            try:
                self.generate_rule_file(rule)
            except Exception as e:
                print(f"Error generating rule file: {str(e)}")


def main():
    # Get the current directory
    current_dir = Path(__file__).parent

    # Setup paths
    json_path = "src/usdm4/rules/rules_v3-10.json"
    output_dir = "src/usdm4/rules/library"

    # Create and run generator
    generator = RuleGenerator(str(json_path), str(output_dir))
    generator.generate_all_rules()

    print("Rule files generated successfully!")


if __name__ == "__main__":
    main()

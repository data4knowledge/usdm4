import os
import json
import pathlib
from urllib.parse import quote

from jsonschema import ValidationError
from jsonschema.exceptions import best_match
from jsonschema.validators import validator_for
from referencing import Registry
from referencing.jsonschema import DRAFT202012


class SchemaValidation:
    class Dummy(ValidationError):
        """Include so ruff doesnot complain about the ValidationError class not being used. Want it to be propagated."""

        pass

    def __init__(self, schema_file_path: str):
        self.schema_file_path = schema_file_path
        with open(schema_file_path, "r") as f:
            self.schema = json.load(f)

        # Register the whole file so that $ref references within it resolve
        self.schema_uri = pathlib.Path(os.path.abspath(schema_file_path)).as_uri()
        self.registry = Registry().with_resource(
            self.schema_uri, DRAFT202012.create_resource(self.schema)
        )

    def get_component_schema(self, component_name):
        if (
            "components" not in self.schema
            or "schemas" not in self.schema["components"]
        ):
            raise ValueError("Schema does not contain components/schemas section")

        if component_name not in self.schema["components"]["schemas"]:
            raise ValueError(f"Schema component '{component_name}' not found")

        return self.schema["components"]["schemas"][component_name]

    def validate_against_component(self, data, component_name):
        component_schema = self.get_component_schema(component_name)
        cls = validator_for(component_schema)
        cls.check_schema(component_schema)
        # Entered by reference, not as the bare component, so that the component's
        # own "#/components/..." references are read against the whole file.
        pointer = component_name.replace("~", "~0").replace("/", "~1")
        root = {"$ref": f"{self.schema_uri}#/components/schemas/{quote(pointer)}"}
        error = best_match(cls(root, registry=self.registry).iter_errors(data))
        if error is not None:
            raise error
        return True

    def validate_file(self, json_file_path, component_name):
        with open(json_file_path, "r") as f:
            data = json.load(f)
        return self.validate_against_component(data, component_name)

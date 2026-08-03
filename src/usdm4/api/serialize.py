import enum
import datetime
from uuid import UUID
from pydantic import BaseModel


# Example, see https://stackoverflow.com/questions/10252010/serializing-class-instance-to-json
def serialize_as_json(obj: BaseModel):
    if isinstance(obj, enum.Enum):
        return obj.value
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif (
        hasattr(obj, "instanceType")
        and getattr(obj, "instanceType") == "ExtensionAttribute"
    ):
        obj_dict: dict = obj.__dict__
        return {k: v for k, v in obj_dict.items() if v is not None}
    else:
        return obj.__dict__

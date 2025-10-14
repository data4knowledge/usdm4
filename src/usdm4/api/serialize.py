import enum
import datetime
from uuid import UUID


# Example, see https://stackoverflow.com/questions/10252010/serializing-class-instance-to-json
def serialize_as_json(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    else:
        return obj.__dict__

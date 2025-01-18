from typing import Literal
from .identifier import Identifier


class AdministrableProductIdentifier(Identifier):
    instanceType: Literal["AdministrableProductIdentifier"]

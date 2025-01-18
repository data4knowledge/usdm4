from usdm4.api import __all__ as api_classes
from usdm3.base.errors import Errors
from usdm3.base.id_manager import IdManager

class Globals():

  def __init__(self):
    self.errors = None
    self.id_manager = None

  def clear(self):
    self.errors = Errors()
    self.id_manager = IdManager(api_classes)
    
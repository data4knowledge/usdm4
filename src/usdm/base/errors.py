import traceback
from d4k_sel.errors import Errors as SelErrors
from d4k_sel.error_location import ErrorLocation as SelErrorLocation


class Errors:
    WARNING = SelErrors.WARNING
    ERROR = SelErrors.ERROR
    DEBUG = SelErrors.DEBUG
    INFO = SelErrors.INFO

    def __init__(self):
        self.errors = SelErrors()

    def exception(self, message: str, e: Exception, location: SelErrorLocation):
        print(f"Exception: {e}")
        message = f"Exception '{e}' raised. {message}"
        self.errors.add(message, location, self.errors.ERROR)
        message = f"Tracsback for the previous error:\n\n{traceback.format_exc()}"
        self.errors.add(message, location, self.errors.ERROR)

    def error(self, message: str, location: SelErrorLocation):
        self.errors.add(message, location, self.errors.ERROR)

    def warning(self, message: str, location: SelErrorLocation):
        self.errors.add(message, location, self.errors.WARNING)

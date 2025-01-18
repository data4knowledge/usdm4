from d4k_sel.error_location import KlassMethodLocation
from usdm.base.globals import Globals


class APIInstance:
    def __init__(self, globals: Globals):
        self._globals = globals

    def create(self, klass, params):
        try:
            klass_name = klass if isinstance(klass, str) else klass.__name__
            params["id"] = (
                self._globals.id_manager.build_id(klass_name)
                if "id" not in params
                else params["id"]
            )
            params["instanceType"] = klass_name
            return klass(**params)
        except Exception as e:
            loc = KlassMethodLocation("APIInstance", "create")
            self._globals.errors.exception(
                f"Error creating {klass} API instance", e, loc
            )
            return None

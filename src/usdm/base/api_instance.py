class APIInstance:
    def __init__(self, globals):
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
            self._globals.errors.exception(e)
            return None

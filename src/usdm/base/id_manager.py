class IdManager:
    def __init__(self, classes: list[str]):
        self._classes = classes
        self._id_index = {}
        self.clear()

    def clear(self):
        for klass in self._classes:
            self._id_index[klass] = 0

    def build_id(self, klass):
        klass_name = klass if isinstance(klass, str) else str(klass.__name__)
        self._id_index[klass_name] += 1
        return f"{klass_name}_{self._id_index[klass_name]}"

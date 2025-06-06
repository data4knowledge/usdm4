class Library:
    def __init__(self, root_path: str):
        self.system = "ISO 639-1"
        self.version = "2007"

    def load(self) -> None:
        pass

    def decode(self, code: str) -> str | None:
        # Just support "en" for the moment
        return "English" if code == "en" else None

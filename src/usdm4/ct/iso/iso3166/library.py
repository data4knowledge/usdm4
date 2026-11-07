import json
import os


class Library:
    BASE_PATH = "ct/iso/iso3166"

    def __init__(self, root_path: str):
        self.system = "ISO 3166 1 alpha3"
        self.version = "2020-08"
        self.filepath = os.path.join(root_path, self.BASE_PATH, "iso3166.json")
        self.db = None

    def load(self) -> None:
        f = open(self.filepath)
        self.db = json.load(f)

    def code_or_decode(self, text: str) -> tuple[str | None, str | None]:
        code, name = self._get_decode(text)
        if not code:
            code, name = self._get_code(text)
        return code, name

    def code(self, decode: str) -> tuple[str | None, str | None]:
        return self._get_code(decode)

    def decode(self, code: str) -> tuple[str | None, str | None]:
        return self._get_decode(code)

    def region_code(self, text: str) -> tuple[str | None, str | None]:
        """The code and name of a region, given its name or its code."""
        return self._get_region(text)

    def _get_decode(self, code: str) -> tuple[str | None, str | None]:
        field = "alpha-2" if len(code) == 2 else "alpha-3"
        entry = next((item for item in self.db if item[field] == code), None)
        return (None, None) if entry is None else (entry["alpha-3"], entry["name"])

    def _get_code(self, decode: str) -> tuple[str | None, str | None]:
        entry = next(
            (item for item in self.db if item["name"].upper() == decode.upper()), None
        )
        return (None, None) if entry is None else (entry["alpha-3"], entry["name"])

    def _get_region(self, text: str) -> tuple[str | None, str | None]:
        value = text.upper()
        for scope in ["region", "sub-region", "intermediate-region"]:
            entry = next(
                (
                    item
                    for item in self.db
                    if value in (item[scope].upper(), item[f"{scope}-code"])
                ),
                None,
            )
            if entry:
                return entry[f"{scope}-code"], entry[scope]
        return None, None

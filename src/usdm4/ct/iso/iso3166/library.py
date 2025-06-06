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

    def decode(self, code: str) -> tuple[str | None, str | None]:
        return self._get_decode(code)

    def region_code(self, decode: str) -> tuple[str | None, str | None]:
        code, decode = self._get_region_decode(decode)
        return code, decode

    def _get_decode(self, code: str) -> tuple[str | None, str | None]:
        if len(code) == 2:
            field = "alpha-2"
        else:
            field = "alpha-3"
        entry = next((item for item in self.db if item[field] == code), None)
        if entry is None:
            return None, None
        else:
            return entry["alpha-3"], entry["name"]

    def _get_region_decode(self, decode: str) -> tuple[str | None, str | None]:
        for scope in ["region", "sub-region", "intermediate-region"]:
            entry = next(
                (item for item in self.db if item[scope].upper() == decode.upper()),
                None,
            )
            if entry:
                return entry[f"{scope}-code"], entry[scope]
        return None, None

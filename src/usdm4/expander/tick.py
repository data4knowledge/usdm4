class Tick:
    def __init__(self, duration: str = None, value: int = None):
        if duration:
            self._tick = self._duration_to_ticks(duration)
        elif value:
            self._tick = value
        else:
            self._tick = 0

    @property
    def tick(self):
        return self._tick

    def __str__(self) -> str:
        intervals = (
            ("weeks", 604800),  # 60 * 60 * 24 * 7
            ("days", 86400),  # 60 * 60 * 24
            ("hours", 3600),  # 60 * 60
            ("minutes", 60),
            ("seconds", 1),
        )
        result = []
        seconds = self._tick
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append("{} {}".format(value, name))
        return ", ".join(result)

    def _duration_to_ticks(self, duration: str) -> int:
        if duration.startswith("PT"):
            if duration.endswith("H"):
                return int(duration[2:-1]) * 60 * 60
            elif duration.endswith("M"):
                return int(duration[2:-1]) * 60
            elif duration.endswith("S"):
                return int(duration[2:-1])
            else:
                raise Exception(f"Failed to decode duration '{duration}")
        else:
            if duration.endswith("Y"):
                return int(duration[1:-1]) * 365 * 24 * 60 * 60
            elif duration.endswith("M"):
                return int(duration[1:-1]) * 30 * 24 * 60 * 60
            elif duration.endswith("W"):
                return int(duration[1:-1]) * 7 * 24 * 60 * 60
            elif duration.endswith("D"):
                return int(duration[1:-1]) * 24 * 60 * 60
            else:
                raise Exception(f"Failed to decode duration '{duration}")

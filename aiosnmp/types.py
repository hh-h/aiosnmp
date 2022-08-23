class Gauge32:
    def __init__(self, val: int):
        if val < 0 or val > 4294967295:
            raise Gauge32ValueError("rfc1902: Gauge32 is a positive int between 0 and 4294967295")
        self._value = val

    def get_value(self) -> int:
        return self._value


class Gauge32ValueError(ValueError):
    """A Value Error related to the SNMP Gauge32 type."""

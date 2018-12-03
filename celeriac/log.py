from typing import Text  # noqa: F401, pylint: disable=unused-import


class Log:
    """Represents an event log."""

    __slots__ = (
        '_severity',
        '_facility',
        '_application',
        '_host',
        '_pid',
        '_message',
    )

    def __init__(self, severity, facility, application, host, pid, message):
        # type: (str, str, str, str, int, Text) -> None
        self._severity = severity  # type: str
        self._facility = facility  # type: str
        self._application = application  # type: str
        self._host = host  # type: str
        self._pid = pid  # type: int
        self._message = message  # type: Text

    @property
    def severity(self):
        # type: () -> str
        return self._severity

    @property
    def facility(self):
        # type: () -> str
        return self._facility

    @property
    def application(self):
        # type: () -> str
        return self._application

    @property
    def host(self):
        # type: () -> str
        return self._host

    @property
    def pid(self):
        # type: () -> int
        return self._pid

    @property
    def message(self):
        # type: () -> Text
        return self._message

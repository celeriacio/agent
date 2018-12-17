from typing import Text


class Log:
    """Represents an event log."""

    __slots__ = (
        '_severity',
        '_facility',
        '_application',
        '_host',
        '_pid',
        '_message',
        '_timestamp',
    )

    def __init__(self, severity, facility, application, host, pid, timestamp, message):
        # type: (str, str, str, str, int, int, Text) -> None
        self._severity = severity
        self._facility = facility
        self._application = application
        self._host = host
        self._pid = pid
        self._timestamp = timestamp
        self._message = message

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
    def timestamp(self):
        # type: () -> int
        return self._timestamp

    @property
    def message(self):
        # type: () -> Text
        return self._message

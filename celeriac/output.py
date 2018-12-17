from abc import ABCMeta, abstractproperty
try:
    import queue
except ImportError:  # pragma: nocover
    import Queue as queue  # type:ignore

from six import with_metaclass

from .log import Log


class OutputABC(with_metaclass(ABCMeta)):
    def __init__(self):
        # type: () -> None
        self._queue = queue.Queue()  # type: queue.Queue[Log]

    def put(self, item):
        # type: (Log) -> None
        self._queue.put(item)

    @abstractproperty
    def supports_logs(self):  # pragma: nocover
        # type: () -> bool
        return False

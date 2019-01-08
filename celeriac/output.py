from abc import ABCMeta, abstractproperty
from typing import Union

try:
    import queue
except ImportError:  # pragma: nocover
    import Queue as queue  # type:ignore

from six import with_metaclass

from .metrics import OnlineWorkers
from .log import Log

OutputItemType = Union[Log, OnlineWorkers]


class OutputABC(with_metaclass(ABCMeta)):
    def __init__(self):
        # type: () -> None
        self._queue = queue.Queue()  # type: queue.Queue[OutputItemType]

    def put(self, item):
        # type: (OutputItemType) -> None
        self._queue.put(item)

    @abstractproperty
    def supports_logs(self):  # pragma: nocover
        # type: () -> bool
        return False

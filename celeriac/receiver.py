import logging
from types import TracebackType
from typing import Optional, Type, Dict, Any

from celery import Celery

from .log import Log
from .output import OutputABC

LOG = logging.getLogger(__name__)


class Receiver:
    def __init__(self, celery, output, application):
        # type: (Celery, OutputABC, str) -> None
        self._celery = celery
        self._state = self._celery.events.State()
        self._output = output
        self._application = application
        self._connection = self._celery.connection_for_read()

    def __enter__(self):
        # type: () -> Receiver
        self._connection.connect()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[TracebackType]) -> bool
        self._connection.release()
        return False

    @staticmethod
    def _convert_timestamp(timestamp):
        # type: (float) -> int
        return int(timestamp * 1e9)

    def _handle_worker_online(self, event):
        # type: (Dict[str, Any]) -> None
        LOG.debug(event)

        if self._output.supports_logs:
            item = Log(
                severity='info',
                facility='worker',
                application=self._application,
                host=event['hostname'],
                pid=event['pid'],
                timestamp=self._convert_timestamp(event['timestamp']),
                message=u'Worker ({0[sw_sys]} {0[sw_ident]} {0[sw_ver]}) is online'.format(event),
            )
            self._output.put(item)
        else:
            LOG.warning('%s does not support logs', self._output.__class__.__name__)

    def _handle_worker_offline(self, event):
        # type: (Dict[str, Any]) -> None
        LOG.debug(event)

        if self._output.supports_logs:
            item = Log(
                severity='info',
                facility='worker',
                application=self._application,
                host=event['hostname'],
                pid=event['pid'],
                timestamp=self._convert_timestamp(event['timestamp']),
                message=u'Worker is offline',
            )
            self._output.put(item)
        else:
            LOG.warning('%s does not support logs', self._output.__class__.__name__)

    def _handle_worker_heartbeat(self, event):
        # type: (Dict[str, Any]) -> None
        LOG.debug(event)

        if self._output.supports_logs:
            item = Log(
                severity='debug',
                facility='worker',
                application=self._application,
                host=event['hostname'],
                pid=event['pid'],
                timestamp=self._convert_timestamp(event['timestamp']),
                message=u'Worker sent a heartbeat',
            )
            self._output.put(item)
        else:
            LOG.warning('%s does not support logs', self._output.__class__.__name__)

    def capture(self):
        # type: () -> None
        receiver = self._celery.events.Receiver(self._connection, handlers={
            'worker-online': self._handle_worker_online,
            'worker-offline': self._handle_worker_offline,
            'worker-heartbeat': self._handle_worker_heartbeat,
        })
        receiver.capture()

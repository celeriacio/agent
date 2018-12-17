# pylint: disable=redefined-outer-name, unused-argument
import logging
from threading import Thread

import pytest

from celeriac.output import OutputABC
from celeriac.receiver import Receiver


class OutputWithLogs(OutputABC):
    @property
    def supports_logs(self):
        return True

    @property
    def queue(self):
        return self._queue


class OutputWithoutLogs(OutputWithLogs):
    @property
    def supports_logs(self):
        return False


@pytest.fixture
def output_with_logs():
    return OutputWithLogs()


@pytest.fixture
def output_without_logs():
    return OutputWithoutLogs()


@pytest.fixture
def receiver(celery_app):
    class ReceiverThread(Thread):
        def __init__(self, output):
            self._output = output

            super(ReceiverThread, self).__init__()
            self.daemon = True

        def run(self):
            with Receiver(celery_app, self._output, 'test') as receiver:
                receiver.capture()

    return ReceiverThread


@pytest.fixture
def worker(celery_app):
    worker = celery_app.Worker(pool='solo', concurrency=1)
    thread = Thread(target=worker.start)
    thread.daemon = True
    thread.start()

    yield worker

    celery_app.control.broadcast('shutdown')
    thread.join()


def test_contextmanager(celery_app, output_without_logs):
    with Receiver(celery_app, output_without_logs, 'test'):
        pass


def test_worker_online_with_logs(caplog, worker, receiver, output_with_logs):
    caplog.set_level(logging.DEBUG)

    receiver(output_with_logs).start()

    log = output_with_logs.queue.get()

    assert log.severity == 'info'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert 'is online' in log.message
    assert log.host
    assert log.pid
    assert log.timestamp


def test_receiver_without_logs(caplog, worker, receiver, output_without_logs):
    caplog.set_level(logging.DEBUG)

    receiver(output_without_logs).start()


def test_worker_heartbeat_with_logs(caplog, worker, receiver, output_with_logs):
    caplog.set_level(logging.DEBUG)

    receiver(output_with_logs).start()

    for _ in range(2):
        log = output_with_logs.queue.get()
        if log.message == 'Worker sent a heartbeat':
            break
    else:
        pytest.fail('Heartbeat event was not found')

    assert log.severity == 'debug'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert log.host
    assert log.pid
    assert log.timestamp


def test_worker_offline_with_logs(caplog, worker, receiver, output_with_logs):
    caplog.set_level(logging.DEBUG)

    receiver(output_with_logs).start()
    worker.app.control.broadcast('shutdown')

    for _ in range(3):
        log = output_with_logs.queue.get()
        if log.message == 'Worker is offline':
            break
    else:
        pytest.fail('Worker offline event was not found')

    assert log.severity == 'info'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert log.host
    assert log.pid
    assert log.timestamp

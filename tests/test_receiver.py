# pylint: disable=redefined-outer-name, unused-argument
from functools import partial
import logging
from threading import Thread
try:
    import queue
except ImportError:
    import Queue as queue

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
def receiver_thread(celery_session_app):
    class ReceiverThread(Thread):
        def __init__(self, output):
            self._receiver = None
            self.output = output

            super(ReceiverThread, self).__init__()
            self.daemon = True

        def run(self):
            with Receiver(celery_session_app, self.output, 'test') as receiver:
                self._receiver = receiver
                self._receiver.capture()

        def stop(self):
            if self._receiver:
                self._receiver.stop()
                self.join()

    return ReceiverThread


@pytest.fixture
def receiver_with_logs(receiver_thread, output_with_logs):
    receiver = receiver_thread(output_with_logs)

    receiver.start()
    yield receiver
    receiver.stop()


@pytest.fixture
def receiver_without_logs(receiver_thread, output_without_logs):
    receiver = receiver_thread(output_without_logs)

    receiver.start()
    yield receiver
    receiver.stop()


# We'd love to use celery_worker fixture instead.
# But for some reason the receiver doesn't capture any events when using it.
@pytest.fixture
def worker_thread(celery_session_app):
    class WorkerThread(Thread):
        def __init__(self):
            self.worker = celery_session_app.Worker(pool='solo', concurrency=1)
            self.worker.shutdown = partial(celery_session_app.control.shutdown, [self.worker.hostname])

            super(WorkerThread, self).__init__()
            self.daemon = True

        def run(self):
            self.worker.start()

        def stop(self):
            self.worker.shutdown()
            self.join()

    thread = WorkerThread()
    yield thread
    thread.stop()


@pytest.fixture
def worker(worker_thread):
    worker_thread.start()
    yield worker_thread.worker


def test_worker_online_with_logs(caplog, worker_thread, receiver_with_logs):
    caplog.set_level(logging.DEBUG)
    worker_thread.start()

    try:
        log = receiver_with_logs.output.queue.get(timeout=10)
    except queue.Empty:
        pytest.fail('Timeout waiting for an event')

    assert log.severity == 'info'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert 'is online' in log.message
    assert log.host == worker_thread.worker.hostname
    assert log.pid
    assert log.timestamp


def test_worker_heartbeat_with_logs(caplog, worker, receiver_with_logs):
    caplog.set_level(logging.DEBUG)

    for _ in range(2):
        try:
            log = receiver_with_logs.output.queue.get(timeout=10)
        except queue.Empty:
            pytest.fail('Timeout waiting for an event')

        if log.message == 'Worker sent a heartbeat':
            break
    else:
        pytest.fail('Heartbeat event was not found')

    assert log.severity == 'debug'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert log.host == worker.hostname
    assert log.pid
    assert log.timestamp


def test_worker_offline_with_logs(caplog, worker, receiver_with_logs):
    caplog.set_level(logging.DEBUG)
    worker.shutdown()

    for _ in range(3):
        try:
            log = receiver_with_logs.output.queue.get(timeout=10)
        except queue.Empty:
            pytest.fail('Timeout waiting for an event')

        if log.message == 'Worker is offline':
            break
    else:
        pytest.fail('Worker offline event was not found')

    assert log.severity == 'info'
    assert log.facility == 'worker'
    assert log.application == 'test'
    assert log.host == worker.hostname
    assert log.pid
    assert log.timestamp

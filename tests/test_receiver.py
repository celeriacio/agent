# pylint: disable=redefined-outer-name, unused-argument
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
            self.worker.shutdown = celery_session_app.control.shutdown

            super(WorkerThread, self).__init__()

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


def test_output_worker_online_log(caplog, worker_thread, receiver_with_logs):
    caplog.set_level(logging.DEBUG)
    worker_thread.start()

    try:
        item = receiver_with_logs.output.queue.get(timeout=10)
    except queue.Empty:
        pytest.fail('Timeout waiting for an event')

    assert item.severity == 'info'
    assert item.facility == 'worker'
    assert item.application == 'test'
    assert 'is online' in item.message
    assert item.host == worker_thread.worker.hostname
    assert item.pid
    assert item.timestamp


def test_output_worker_online_metric(caplog, worker_thread, receiver_without_logs):
    caplog.set_level(logging.DEBUG)
    worker_thread.start()

    try:
        item = receiver_without_logs.output.queue.get(timeout=10)
    except queue.Empty:
        pytest.fail('Timeout waiting for a metric')

    assert item.labels.application == 'test'
    assert item.labels.host == worker_thread.worker.hostname
    assert item.values.online == 1
    assert item.timestamp


def test_output_worker_heartbeat_log(caplog, worker, receiver_with_logs):
    caplog.set_level(logging.DEBUG)

    # We expect to receive at most 3 items:
    #   worker-online log
    #   worker-online metric
    #   worker-heartbeat log
    for _ in range(3):
        try:
            item = receiver_with_logs.output.queue.get(timeout=10)
        except queue.Empty:
            pytest.fail('Timeout waiting for a log')

        if getattr(item, 'message', None) == 'Worker sent a heartbeat':
            break
    else:
        pytest.fail('Heartbeat log was not found')

    assert item.severity == 'debug'
    assert item.facility == 'worker'
    assert item.application == 'test'
    assert item.host == worker.hostname
    assert item.pid
    assert item.timestamp


def test_output_worker_offline_log(caplog, worker, receiver_with_logs):
    caplog.set_level(logging.DEBUG)
    worker.shutdown()

    # We expect to receive at most 5 items:
    #   worker-online log
    #   worker-online metric
    #   worker-heartbeat log
    #   worker-heartbeat metric
    #   worker-offline log
    for _ in range(5):
        try:
            item = receiver_with_logs.output.queue.get(timeout=10)
        except queue.Empty:
            pytest.fail('Timeout waiting for a log')

        if getattr(item, 'message', None) == 'Worker is offline':
            break
    else:
        pytest.fail('Worker offline log was not found')

    assert item.severity == 'info'
    assert item.facility == 'worker'
    assert item.application == 'test'
    assert item.host == worker.hostname
    assert item.pid
    assert item.timestamp


def test_output_worker_offline_metric(caplog, worker, receiver_without_logs):
    caplog.set_level(logging.DEBUG)
    worker.shutdown()

    # We expect to receive at most 2 items:
    #   worker-online metric
    #   worker-offline metric
    for _ in range(2):
        try:
            item = receiver_without_logs.output.queue.get(timeout=10)
        except queue.Empty:
            pytest.fail('Timeout waiting for a metric')

        if item.values.online == 0:
            break
    else:
        pytest.fail('Worker offline metric was not found')

    assert item.labels.application == 'test'
    assert item.labels.host == worker.hostname
    assert item.timestamp

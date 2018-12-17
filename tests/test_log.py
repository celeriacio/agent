# -*- coding: utf-8 -*-
from time import time

from celeriac.log import Log


def test():
    severity = 'info'
    facility = 'worker'
    application = 'test_app'
    host = 'test_host'
    pid = 123
    timestamp = time()
    message = u'Hello 🌎'

    log = Log(severity, facility, application, host, pid, timestamp, message)

    assert log.severity == severity
    assert log.facility == facility
    assert log.application == application
    assert log.host == host
    assert log.pid == pid
    assert log.timestamp == timestamp
    assert log.message == message

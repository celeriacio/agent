from typing import Text, NamedTuple

Log = NamedTuple('Log', (
    ('severity', str),
    ('facility', str),
    ('application', str),
    ('host', str),
    ('pid', int),
    ('timestamp', int),
    ('message', Text),
))

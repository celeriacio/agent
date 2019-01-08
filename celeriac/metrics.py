from typing import Union, Text, NamedTuple

LabelType = Text
ValueType = Union[float, int]

OnlineWorkersLabels = NamedTuple('OnlineWorkersLabels', (
    ('application', LabelType),
    ('host', LabelType),
))
OnlineWorkersValues = NamedTuple('OnlineWorkersValues', (
    ('online', ValueType),
))
OnlineWorkers = NamedTuple('OnlineWorkersMetric', (
    ('timestamp', int),
    ('labels', OnlineWorkersLabels),
    ('values', OnlineWorkersValues),
))

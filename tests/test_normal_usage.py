from enum import Enum
import json
import pytest
from typing import Dict, List, Literal, Optional

from implicitdict import ImplicitDict, StringBasedDateTime, StringBasedTimeDelta


class MyData(ImplicitDict):
    foo: str
    bar: int = 0
    baz: Optional[float]


def test_basic_usage():
    # Most basic usage is to parse a plain dict into an ImplicitDict...
    data: MyData = ImplicitDict.parse({'foo': 'asdf', 'bar': 1}, MyData)
    # ...and implicitly serialize the ImplicitDict to a plain dict
    assert json.dumps(data) == '{"foo": "asdf", "bar": 1}'

    # Fields can be referenced directly...
    assert data.foo == 'asdf'
    assert data.bar == 1
    # ...or implicitly by name (because the object is implicitly a dict)
    assert data['foo'] == 'asdf'
    assert data['bar'] == 1

    # Optional fields that aren't specified simply don't exist
    assert 'baz' not in data
    with pytest.raises(KeyError):
        assert data.baz == 0

    # Optional fields can be omitted (fields with defaults are optional)
    data = MyData(foo='asdf')
    assert json.loads(json.dumps(data)) == {'foo': 'asdf', 'bar': 0}

    # Optional fields can be specified
    data = ImplicitDict.parse({'foo': 'asdf', 'baz': 1.23}, MyData)
    assert json.loads(json.dumps(data)) == {'foo': 'asdf', 'bar': 0, 'baz': 1.23}
    assert 'baz' in data
    assert data.baz == 1.23

    # Failing to specify a required field ("foo") raises a ValueError
    with pytest.raises(ValueError):
        MyData(bar=1)


class MyIntEnum(int, Enum):
    Value1 = 1
    Value2 = 2
    Value3 = 3


class MyStrEnum(str, Enum):
    Value1 = 'foo'
    Value2 = 'bar'
    Value3 = 'baz'


class Features(ImplicitDict):
    int_enum: MyIntEnum
    str_enum: MyStrEnum
    t_start: StringBasedDateTime
    my_duration: StringBasedTimeDelta
    my_literal: Literal['Must be this string']
    nested: Optional[MyData]


def test_features():
    src_dict = {
        'int_enum': 2,
        'str_enum': 'baz',
        't_start': '2022-01-01T01:23:45.6789Z',
        'my_duration': '1:23:45.67',
        'my_literal': 'Must be this string',
        'nested': {
            'foo': 'asdf'
        },
        'unrecognized_fields': 'are simply ignored'
    }
    data: Features = ImplicitDict.parse(src_dict, Features)

    assert data.int_enum == MyIntEnum.Value2
    assert data.int_enum == 2

    assert data.str_enum == MyStrEnum.Value3
    assert data.str_enum == 'baz'

    assert data.t_start.datetime.year == 2022
    assert data.t_start.datetime.month == 1
    assert data.t_start.datetime.day == 1
    assert data.t_start.datetime.hour == 1
    assert data.t_start.datetime.minute == 23
    assert data.t_start.datetime.second == 45
    assert data.t_start.datetime.microsecond == 678900

    assert data.my_duration.timedelta.total_seconds() == 1 * 3600 + 23 * 60 + 45.67

    assert data.my_literal == 'Must be this string'

    assert 'nested' in data

    src_dict['my_literal'] = 'Not that string'
    with pytest.raises(ValueError):
        ImplicitDict.parse(src_dict, Features)


class NestedStructures(ImplicitDict):
    my_list: List[MyData]
    my_dict: Dict[str, List[float]]


def test_nested_structures():
    src_dict = {
        'my_list': [{'foo': 'one'}, {'foo': 'two'}],
        'my_dict': {'foo': 1.23, 'bar': 4.56}
    }
    data: NestedStructures = ImplicitDict.parse(src_dict, NestedStructures)

    assert len(data.my_list) == 2
    assert data.my_list[0].foo == 'one'
    assert data.my_list[1].foo == 'two'

    assert len(data.my_dict) == 2
    assert data.my_dict['foo'] == 1.23
    assert data.my_dict['bar'] == 4.56

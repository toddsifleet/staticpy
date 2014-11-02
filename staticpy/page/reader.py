from __future__ import absolute_import

import re
import os
from datetime import datetime

from .data import Data

NAME_REGEX = re.compile(
    r'^:(?P<attribute>[a-z\-_]+)'
    r'(?:\[(?P<type>[a-z]+)\])?:'
    r'\s*(?P<value>.*)$'
)


def _read_file(path):
    with open(path) as fp:
        return fp.readlines()


def _to_list(value):
    if not value:
        return []
    lines = value.split('\n')
    return [x.strip() for x in lines]


def _cast(value, data_type):
    value = value.strip()
    if data_type == 'list':
        value = _to_list(value)
    if data_type == 'int':
        value = int(value)
    return value


class Reader(object):
    def __init__(self, path):
        self.path = path

    def read(self):
        output = Data()

        attribute, value, data_type = '', '', None
        for line in _read_file(self.path):
            data = NAME_REGEX.match(line)
            if data:
                if value:
                    output.set(
                        attribute,
                        _cast(value, data_type),
                    )

                attribute = data.group('attribute')
                value = data.group('value')
                data_type = data.group('type')
            else:
                value += line
        output.set(
            attribute,
            _cast(value, data_type),
        )
        return output

    @property
    def _created_at(self):
        created_at = os.path.getctime(self.path)
        return datetime.fromtimestamp(created_at)

    @property
    def _modified_at(self):
        modified_at = os.path.getmtime(self.path)
        return datetime.fromtimestamp(modified_at)

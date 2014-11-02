from __future__ import absolute_import


class Data(object):
    def __init__(self, **kwargs):
        self._data = kwargs

    def set(self, name, value):
        name = name.strip().replace('-', '_')
        self._data[name] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getattr__(self, name):
        return self._data.get(name, '')

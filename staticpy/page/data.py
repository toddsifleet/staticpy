class Data(object):
    def __init__(self, **kwargs):
        self._data = {}

    def set(self, name, value):
        name = name.strip().replace('-', '_')
        self._data[name] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    @property
    def order(self):
        return int(self.get('order', 100))

    def __getattr__(self, name):
        return self._data.get(name, '')

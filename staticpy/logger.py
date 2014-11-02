from __future__ import absolute_import

from functools import wraps
from datetime import datetime

color_codes = {
    'INFO': '\033[94m',
    'WARNING': '\033[93m',
    'SUCCESS': '\033[92m',
    'ERROR': '\033[91m',
}


def log_method(func):
    @wraps(func)
    def wrapped(instance, value, *args, **kwargs):
        value = value.format(*args, **kwargs)
        return func(instance, value)
    return wrapped


def print_with_color(value, color):
    value = "{color} [{time}] {value}\033[0m".format(
        color=color_codes[color],
        time=datetime.now().strftime("%H:%M:%S"),
        value=value,
    )
    print value


class Logger(object):

    @log_method
    def info(self, value):
        print_with_color(value, 'INFO')

    @log_method
    def warning(self, value):
        print_with_color(value, 'WARNING')

    @log_method
    def success(self, value):
        print_with_color(value, 'SUCCESS')

    @log_method
    def error(self, value):
        print_with_color(value, 'ERROR')

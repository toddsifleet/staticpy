from __future__ import absolute_import

import os
from os.path import isdir, isfile
import sys
import shutil

from .logger import Logger

logger = Logger()


class DummySettings(object):
    base_url = ''

    def __init__(self, site_path):
        self.input_path = site_path
        self.output_path = os.path.join(site_path, '.output')


def init_output_dir(site_path, output_path):
    create_output_dir(output_path)
    link_static(site_path, output_path)


def create_output_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def link_static(site_path, output_path):
    try:
        os.symlink(
            os.path.join(site_path, 'static'),
            os.path.join(output_path, 'static')
        )
    except:
        print '%s/static already exists' % output_path


def copy_attrs(target, source, *attrs):
    for a in attrs:
        setattr(target, a, getattr(source, a))


def load_settings(site_path):
    if not os.path.isdir(site_path):
        raise IOError('Could not find the path specified %s' % site_path)

    sys.path.append(site_path)
    try:
        import settings
        settings.output_path = os.path.join(site_path, '.output')
    except ImportError:
        settings = DummySettings(site_path)

    settings.input_path = site_path
    return settings


class cached_property(property):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        if instance._cache is None:
            instance._cache = {}
        elif self.name in instance._cache:
            return instance._cache.get(self.name)
        value = self.func(instance)

        instance._cache[self.name] = value
        return value

    def __set__(self, instance, value):
        if instance._cache is None:
            instance._cache = {}
        instance._cache[self.name] = value


def ensure_directory_exists(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def write_to_file(fp, contents):
    with open(fp, 'w') as output:
        output.write(contents)


def list_directory(path):
    return [os.path.join(path, f) for f in os.listdir(path)]


def list_directories(path):
    paths = list_directory(path)
    return [p for p in paths if isdir(p)]


def list_files(path):
    paths = list_directory(path)
    return [p for p in paths if isfile(p)]

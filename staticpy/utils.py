import os
import sys
import shutil


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
    except:
        settings = DummySettings(site_path)

    settings.input_path = site_path
    return settings

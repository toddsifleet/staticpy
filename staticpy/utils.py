import os
import shutil


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

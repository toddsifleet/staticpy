import os
import sys
import argparse
from functools import wraps

from utils import init_output_dir
from s3_uploader import BulkUploader
from compiler import Site
from socket_server import SocketServer
from web_server import WebServer
from file_monitor import monitor_site


class DummySettings(object):
    base_url = ''

    def __init__(self, site_path):
        self.output_path = os.path.join(site_path, '.output')


def _upload_to_s3(settings):
    '''Upload the site to s3

        Given a settings object with s3 credentials and a bucket name we upload
        the compiled results to s3.

        We transform the individual file paths to remove .html unless they are
        index.html files.  This allows us to have pretty urls like
        /path/to/page.

        params:
            settings
    '''
    def transform(path):
        if path.endswith('index.html'):
            return path
        elif path.endswith('.html'):
            return path[0:-5]
        return path

    def file_filter(path):
        file_name = os.path.basename(path)
        return not file_name.startswith('.')

    BulkUploader(settings, file_filter, transform).start()


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


def parse_args_and_load_settings(func):
    @wraps(func)
    def wrapped():
        parser = argparse.ArgumentParser(
            description='''Compile a directory of site data templates, pags,
            and static files into a static website.  Using -dev and -monitor
            you can have the site recompile on all changes and refresh in
            your browser'''
        )

        parser.add_argument(
            'site_path',
            help="The path to the to your website's data",
        )

        site_path = parser.parse_args().site_path
        settings = load_settings(site_path)
        init_output_dir(site_path, settings.output_path)
        func(settings)
    return wrapped


@parse_args_and_load_settings
def develop(settings):

    socket_server = SocketServer().start()

    WebServer(settings.output_path).start()

    monitor_site(
        compile_site(settings, socket_server.client_js_code, True),
        socket_server.queue
    )


@parse_args_and_load_settings
def upload(settings):
    compile_site(settings)
    if hasattr(settings, 's3_bucket'):
        _upload_to_s3(settings)
    else:
        print "No S3 credentials specified"


def compile_site(settings, client_js_code='', dev=False):
    site = Site(settings, client_js_code, dev)
    print 'Compiling Site: %s' % settings.input_path
    print 'Output: %s' % settings.output_path
    site.compile()
    print 'Done Compiling'
    return site

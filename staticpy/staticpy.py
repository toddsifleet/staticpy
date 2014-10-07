import os
import sys
import argparse
from functools import wraps

from utils import init_output_dir
import compiler
import socket_server
import web_server
import file_monitor


class DummySettings(object):
    base_url = ''

    def __init__(self, site_path):
        self.output_path = os.path.join(site_path, '.output')


def _upload_to_s3(settings):
    '''Upload the site to s3

        Given a site_path, access credentials and an s3 buck name we upload
        the compiled results to s3.

        We transform the individual file paths to remove .html unless they are
        index.html files.  This allows us to have pretty urls like
        /path/to/page.

        We filter out .DS_Store files as well
        params:
            site_path: the path to our files
            aws_keys: ('access_key', 'secret_key')
            bucket: s3 bucket bucket_name
    '''
    from s3_uploader import BulkUploader

    def transform(path):
        if path.endswith('index.html'):
            return path
        elif path.endswith('.html'):
            return path[0:-5]
        return path

    def file_filter(path):
        file_name = os.path.basename(path)
        return not file_name.startswith('.')

    uploader = BulkUploader(
        settings.aws_keys,
        settings.s3_bucket,
        file_filter,
        transform
    )
    uploader.start(settings.output_path)

def load_settings(site_path):
    if not os.path.isdir(site_path):
        raise IOError('Could not find the path specified %s' % site_path)

    sys.path.append(site_path)
    try:
        import settings
        if not hasattr(settings, 'output_path'):
            settings.output_path = os.path.join(site_path, '.output')
    except:
        global settings
        settings = DummySettings(site_path)


def parse_args_and_load_settings(func):
    @wraps(func)
    def wrapped():
        parser = argparse.ArgumentParser(
            description='''Compile a directory of site data templates, pags, and
            static files into a static website.  Using -dev and -monitor you can
            have the site recompile on all changes and refresh in your browser'''
        )

        parser.add_argument(
            'site_path',
            help="The path to the to your website's data",
        )

        site_path = parser.parse_args().site_path
        load_settings(site_path)
        init_output_dir(site_path, settings.output_path)
        func(site_path)
    return wrapped


@parse_args_and_load_settings
def develop(site_path):

    update_server = socket_server.WebSocketServer()
    update_server.start()

    web_server.Server(settings.output_path).start()

    file_monitor.monitor_site(
        compile_site(site_path, update_server.client_js_code, True),
        update_server.queue
    )


@parse_args_and_load_settings
def upload(site_path):
    compile_site(site_path)
    if hasattr(settings, 's3_bucket') and hasattr(settings, 'aws_keys'):
        _upload_to_s3(settings)
    else:
        print "No S3 credentials specified"


def compile_site(site_path, client_js_code='', dev=False):
    site = compiler.Site(site_path, settings, client_js_code, dev)
    print 'Compiling Site: %s' % site_path
    print 'Output: %s' % settings.output_path
    site.compile()
    print 'Done Compiling'
    return site

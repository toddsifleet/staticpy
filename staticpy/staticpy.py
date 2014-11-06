from __future__ import absolute_import

import os
import argparse
from functools import wraps

from .utils import init_output_dir, load_settings, logger
from .s3_uploader import upload_to_s3
from .site import Site
from .socket_server import SocketServer
from .web_server import WebServer
from .file_monitor import monitor_site


def _compile_site(settings, client_js_code='', dev=False):
    site = Site(settings, client_js_code, dev)
    logger.info('Compiling Site: {path}', path=settings.input_path)
    logger.info('Output: %s' % settings.output_path)
    site.save()
    logger.success('Done Compiling')
    return site


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
        site_path = os.path.abspath(site_path)
        settings = load_settings(site_path)
        init_output_dir(site_path, settings.output_path)
        func(settings)
    return wrapped


@parse_args_and_load_settings
def develop(settings):

    socket_server = SocketServer().start()

    WebServer(settings.output_path).start()

    monitor_site(
        _compile_site(settings, socket_server.client_js_code, True),
        socket_server.queue
    )


@parse_args_and_load_settings
def upload(settings):
    _compile_site(settings)
    if hasattr(settings, 's3_bucket'):
        upload_to_s3(
            settings.aws_keys,
            settings.s3_bucket,
            settings.output_path,
        )
    else:
        logger.error("No S3 credentials specified")


if __name__ == '__main__':
    develop()

import argparse
import compiler
import socket_server
import Queue
import os
import sys
from utils import init_output_dir


class DummySettings(object):
    base_url = ''

    def __init__(self, site_path):
        self.output_path = os.path.join(site_path, '.output')


def upload_to_s3(settings):
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


def run(args):
    site_path = args.site_path
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

    init_output_dir(site_path, settings.output_path)

    if args.dev:
        args.serve = True
        args.monitor = True
        clients = Queue.Queue()
        server = socket_server.WebSocketServer(clients)
        client_js_code = server.client_js_code
        server.start()
    else:
        client_js_code = ''
        clients = None

    site = compiler.Site(site_path, settings, client_js_code, args.dev)

    print 'Compiling Site: %s' % site_path
    print 'Output: %s' % settings.output_path
    site.compile()
    print 'Done Compiling'

    if args.upload:
        if hasattr(settings, 's3_bucket') and hasattr(settings, 'aws_keys'):
            upload_to_s3(settings)
        else:
            print '''settings.py must includ:

    aws_keys = ("access_key", "private_key")
    s3_bucket = "bucket_name"


    In order to upload to S3...'''

    if args.serve:
        import web_server
        web_server.Server(settings.output_path).start()

    if args.monitor:
        import file_monitor
        observer = file_monitor.monitor_site(site, clients)

    if args.monitor or args.serve:
        raw_input('Running: press enter to quit...')

        print 'Shutting Down'
        if args.monitor:
            observer.stop()
            observer.join()


def parse_args_and_run():
    parser = argparse.ArgumentParser(
        description='''Compile a directory of site data templates, pags, and
        static files into a static website.  Using -dev and -monitor you can
        have the site recompile on all changes and refresh in your browser'''
    )

    parser.add_argument(
        '-monitor',
        dest='monitor',
        action='store_true',
        help='Monitor your files and automatically update when a file is saved'
    )

    parser.add_argument(
        '-dev',
        dest='dev',
        action='store_true',
        help='''Enable all active development features, including monitor.
        Anything hidden behind and {% if dev %} in your templates will be
        displayed.  Start server to notify browsers of changes'''
    )

    parser.add_argument(
        '-s3',
        dest='upload',
        action='store_true',
        help="Upload to the s3 bucket defined in your site's settings.py file"
    )

    parser.add_argument(
        '-serve',
        dest='serve',
        action='store_true',
        help='Start a basic dev server to serve the static webpages'
    )

    parser.add_argument(
        'site_path',
        help="The path to the to your website's data",
    )

    run(parser.parse_args())

if __name__ == '__main__':
    parse_args_and_run()

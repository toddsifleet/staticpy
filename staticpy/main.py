import argparse
import compiler
import Queue
import socket_server
import os
import sys
import time

import shutil

#dependency (if you want to do anything that has to do with monitoring files check out watchdog)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def upload_to_s3(site_path, aws_keys, bucket):
    '''Upload the site to s3

        Given a site_path, access credentials and an s3 buck name we upload
        the compiled results to s3.  

        We transform the individual file paths to remove .html unless they are 
        index.html files.  This allows us to have pretty urls like /path/to/page.

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
        return not path.endswith('.DS_Store')

    uploader = BulkUploader(aws_keys, bucket, file_filter, transform)
    uploader.start(site_path)

def copy_static(site_path, output_path):
    '''Copy the contents of the static directory from our site_path to our 
    output_path.  If /output_path/static already exists we delete it!'''

    static_dir_in = os.path.join(site_path, 'static')
    if not os.path.isdir(static_dir_in):
        return

    static_dir_out = os.path.join(output_path, 'static')
    if os.path.isdir(static_dir_out):
        shutil.rmtree(static_dir_out)
    shutil.copytree(static_dir_in, static_dir_out)

class FileUpdated(FileSystemEventHandler):
    '''Define callbacks for watchdog

        The callback are:
            static changes: copy new/modified file into output_path/static/..
            dynamic changes: recompile site 

            All changes: If self.clients_queue has entris we loop through each
                client to notify them of the changes, this allows the browser 
                to refresh without user intervention.
    '''
    def __init__(self, clients_queue, site):
        self.clients_queue = clients_queue
        self.site = site
        self.site_path = site.input_path
        self.output_path = site.output_path
        self.static_dir = os.path.join(self.site_path, 'static')        
        FileSystemEventHandler.__init__(self)

    def dispatch(self, file_path):
        file_path = file_path.src_path
        if file_path == self.static_dir:
            print "Copying the static directory"
            copy_static(self.site_path, self.output_path)

        if file_path.startswith(self.static_dir):
            new_file_path = os.path.join(self.output_path, 'static', file_path[len(self.static_dir) + 1::])
            if os.path.isfile(file_path):
                print 'Copying Static File: %s' % new_file_path
                shutil.copy(file_path, new_file_path)
            elif os.path.isfile(new_file_path):
                print 'Deleting File: %s' % new_file_path
                os.remove(new_file_path)
        else:
            try:
                print 'Recompiling Site'
                self.site.navigation_links = []
                self.site.compile()
                print 'Done Recompiling'
            except Exception as e:
                print 'Error Recompiling', e


        if self.clients_queue:
            self.notify()
        
        print 'Running: press enter to quit...'

    def notify(self):
        while not self.clients_queue.empty():
            client = self.clients_queue.get()
            client.send('update')

def monitor_site(site, clients = None):
    '''Monitor site_path for changes

        We start a watchdog observer to monitor the site_path.  Once we are monitoring
        all of the files we sit and wait for user input telling us to exit.

        params:
            site: a compiler.Site object
            clients: a Queue.Queue() containing WebSocket clients

        return:
            None
    '''
    observer = Observer()
    for directory in ['dynamic', 'static']:
        path = os.path.join(site.input_path, directory)
        if os.path.isdir(path):
            observer.schedule(
                FileUpdated(clients, site), 
                path = path, 
                recursive = True
            )

    observer.start()
    input = raw_input('Running: press enter to quit...')

    print 'shutting down'
    observer.stop()
    observer.join()

def get_output_path(site_path):
    if hasattr(settings, 'output_path'):
        output_path = settings.output_path
    else:
        output_path = os.path.join(site_path, 'output')

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    return output_path

def run(args):
    if not os.path.isdir(args.site_path):
        raise IOError('Could not find the path specified %s' % args.path)

    site_path = args.site_path
    sys.path.append(site_path)

    try:
        import settings
    except:
        print 'No settings.py file found'
        global settings
        #it can just be a dummy object, we always verify it has an attribute before getting it
        settings = object()

    output_path = get_output_path(site_path)
    if args.dev:
        args.monitor = True
        clients = Queue.Queue()
        server = socket_server.WebSocketServer(clients)
        dev_host = {
            'host': server.host,
            'port': server.port
        }
        server.start()
    else:
        dev_host = None
        clients = None

    copy_static(site_path, output_path)
    site = compiler.Site(site_path, output_path, dev_host)
    
    print 'Compiling Site: %s' % site_path
    print 'Output: %s' % output_path
    site.compile()
    print 'Done Compiling'

    if args.upload:
        if hasattr(settings, 's3_bucket') and hasattr(settings, 'aws_keys'):
            upload_to_s3(output_path, settings.aws_keys, settings.s3_bucket)
        else:
            print '''You must define a bucket and s3 access credential in your settings.py file
it should take the form:

    aws_keys = ("access_key", "private_key")
    s3_bucket = "bucket_name"'''

    if args.serve:
        import web_server
        web_server.Server(output_path).start()

    if args.monitor:
        monitor_site(site, clients)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = '''Compile a directory of site data templates, pags, and static files into
            a static website.  Using -dev and -monitor you can have the site recompile on all changes
            and refresh in your browser'''
    )

    parser.add_argument(
        '-monitor', 
        dest = 'monitor',
        action = 'store_true',
        help = 'Monitor your pages file and automatically update when a file is saved'
    )

    parser.add_argument(
        '-dev', 
        dest = 'dev',
        action ='store_true',
        help = '''Enable all active development features, including monitor.  Anything hidden behind and {% if dev %} 
            in your templates will be displayed.  Start server to notify browsers of changes'''
    )

    parser.add_argument(
        '-s3', 
        dest = 'upload',
        action = 'store_true',
        help = "Upload to the s3 bucket defined in your site's settings.py file"
    )

    parser.add_argument(
        '-serve',
        dest = 'serve',
        action = 'store_true',
        help = 'Start a basic dev server to serve the static webpages'
    )

    parser.add_argument(
        'site_path', 
        help = "The path to the to your website's data",
    )

    run(parser.parse_args())
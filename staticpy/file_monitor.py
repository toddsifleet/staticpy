import os
import re

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ignore_patterns = [
    r'\.swp$',
]
ignore_patterns = [re.compile(x) for x in ignore_patterns]


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
        self.static_dir = os.path.join(site.input_path, 'static')
        FileSystemEventHandler.__init__(self)

    def dispatch(self, file_path):
        for i in ignore_patterns:
            if i.search(file_path.src_path):
                return
        file_path = file_path.src_path
        if not file_path.startswith(self.static_dir):
            try:
                print 'Recompiling Site'
                self.site.compile()
                print 'Done Recompiling'
            except Exception as e:
                print 'Error Recompiling', e

        if self.clients_queue:
            self.notify()

    def notify(self):
        while not self.clients_queue.empty():
            client = self.clients_queue.get()
            client.send('update')


def monitor_site(site, clients=None, wait=True):
    '''Monitor site_path for changes

    We start a watchdog observer to monitor the site_path.  Once we are
    monitoring all of the files we sit and wait for user input telling us
    to exit.

    params:
        site: a Site object
        clients: a Queue.Queue() containing WebSocket clients
    '''
    observer = Observer()
    for directory in ['dynamic', 'static']:
        path = os.path.join(site.input_path, directory)
        if os.path.isdir(path):
            observer.schedule(
                FileUpdated(clients, site),
                path=path,
                recursive=True
            )

    observer.start()
    if wait:
        raw_input('Running: press enter to quit...')
        print 'Shutting Down'
        observer.stop()
        observer.join()

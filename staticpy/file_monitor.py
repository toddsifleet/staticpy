import os
import re

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from utils import logger

IGNORE = (
    r'\.swp$',
    r'sitemap\.xml$',
)

IGNORE = (re.compile(x) for x in IGNORE)


class FileUpdated(FileSystemEventHandler):
    _last_update = 0
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

    def _check_event(self, event):
        if event.is_directory:
            return True

        for i in IGNORE:
            if i.search(event.src_path):
                return True
        try:
            mod_time = os.path.getctime(event.src_path)
        except OSError:
            return False

        if mod_time - self._last_update < .1:
            self._last_update = mod_time
            return True

    def dispatch(self, event):
        if not self._check_event(event):
            return

        if not event.src_path.startswith(self.static_dir):
            try:
                logger.info('Recompiling Site')
                self.site.save()
                logger.success('Done Recompiling')
            except Exception as e:
                logger.warning('Error Recompiling {error}', error=e)

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
        logger.warning('Running: press enter to quit...')
        raw_input('')
        logger.warning('Shutting Down')
        observer.stop()
        observer.join()

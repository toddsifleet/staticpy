#dependency (if you want to do anything that has to do with monitoring files check out watchdog)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys
from utils import copy_static, copy_file
import re

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
        self.site_path = site.input_path
        self.output_path = site.output_path
        self.static_dir = os.path.join(self.site_path, 'static')        
        FileSystemEventHandler.__init__(self)

    def dispatch(self, file_path):
        for i in ignore_patterns:
            if i.search(file_path.src_path):
                return
        file_path = file_path.src_path
        if file_path == self.static_dir:
            print "Copying the static directory"
            copy_static(self.site_path, self.output_path)

        if file_path.startswith(self.static_dir):
            new_file_path = os.path.join(self.output_path, 'static', file_path[len(self.static_dir) + 1::])
            if os.path.isfile(file_path):
                print 'Copying Static File: %s' % new_file_path
                copy_file(file_path, new_file_path)
                
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
    #dependency (if you want to do anything that has to do with monitoring files check out watchdog)
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
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
    return observer

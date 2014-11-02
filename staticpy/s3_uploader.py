import os
import Queue
import threading

from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from boto.s3.key import Key

from utils import copy_attrs, logger


class BulkUploader:
    '''Multi-Threaded s3 directory BulkUploader

    Walks a directory uploading everyfile to s3, you can apply
    filters/transforms to file paths.  On start we spawn up to max_threads
    threads that each upload independently.

    Before uploading a file we verify that the local version is different than
    the version already in s3, this avoid unneeded uploads.

    params:
        aws_keys: ('access_key', 'secret_key')
        bucket: amazon s3 bucket name
        file_filter: a function that accepts a file path and returns true if
            you want it uploaded
        key_transform: a function that accepts a file path and returns the
            appropriate s3 key_transform
        max_threads: the max number of threads you want to spawn
    '''

    def __init__(
        self,
        settings,
        file_filter=None,
        key_transform=None,
        max_threads=10
    ):
        copy_attrs(self, settings, 'aws_keys', 's3_bucket', 'output_path')

        self.max_threads = max_threads
        self.key_transform = key_transform
        self.file_filter = file_filter

    def start(self):
        queue = Queue.Queue()
        current_keys = set()
        for (path, _, files) in os.walk(self.output_path, followlinks=True):
            for file_name in files:
                file_path = os.path.join(path, file_name)
                if not self.file_filter or self.file_filter(file_path):
                    key = self.transform(file_path)
                    current_keys.add(key)
                    queue.put((key, file_path))

        self.delete_removed_keys(current_keys)
        threads = []
        for i in range(self.max_threads):
            thread = Worker(self.aws_keys, self.s3_bucket, queue)
            threads.append(thread)
            thread.start()

        queue.join()
        for i in threads:
            i.join()

    def transform(self, path):
        '''Standard transform from path to key_transform

        Calls your custom transform if it exists, strips off the base directory
        path from the file path and replaces \ with / so they are valid urls.

        params:
            path: path to file
        returns:
            key: the s3 key
        '''
        if self.key_transform:
            path = self.key_transform(path)
        path = path[len(self.output_path)+1::]
        return path.replace('\\', '/')

    def delete_removed_keys(self, current_keys):
        conn = S3Connection(*self.aws_keys)
        bucket = conn.get_bucket(self.s3_bucket)
        old_keys = set([x.name for x in bucket.list()])
        to_delete = old_keys - current_keys
        for i in to_delete:
            logger.warning('Deleting `{file}` from S3', file=file)
        bucket.delete_keys(to_delete)


class Worker(threading.Thread):
    '''A threaded s3 upload Worker

        Uploads files to s3 that are passed to it through the queue returns
        once the queue is empty.

        Won't upload a specified file if the local MD5 hash is the same as the
        MD5 of the file already on s3.

        params:
            aws_keys: ('access_key', 'secret_key')
            bucket: amazon s3 bucket name
            queue: the Queue to pull the (file_path, file_key) tuples from
    '''
    def __init__(self, aws_keys, bucket, queue):
        self.queue = queue
        self.aws_keys = aws_keys
        self.bucket = bucket
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        self.bucket = Bucket(
            connection=S3Connection(*self.aws_keys),
            name=self.bucket
        )

        for key, file_path in IterQueue(self.queue):
            self.upload(key, file_path)

    def upload(self, key, file_path):
        s3_key = self.bucket.get_key(key)
        if s3_key:
            old_hash = s3_key.etag.strip('"')
        else:
            s3_key = Key(self.bucket)
            s3_key.key = key
            old_hash = None

        with open(file_path) as fh:
            new_hash, _ = s3_key.compute_md5(fh)
            if new_hash == old_hash:
                logger.info("File {file} unchanged", file=file)
            else:
                s3_key.set_contents_from_file(fh)
                logger.success('Uploaded: {key}', key=key)


class IterQueue:
    '''Iterate through a Queue.Queue instance

        This allows for easy iteration throught a queue. You don't need
        to worry about setting anything up.  Runs untill the queue is empty

        Calls Queue.task_done when you get the next item.  If you exit the loop
        early you must call task_done yourself on the queue or queue.join will
        block.

        Example usage:
            for i in IterQueue(queue):
                do_something(i)
    '''
    def __init__(self, queue):
        self.queue = queue

    def __iter__(self):
        self.task_in_progress = False
        return self

    def next(self):
        if self.task_in_progress:
            self.queue.task_done()
        try:
            r = self.queue.get_nowait()
            self.task_in_progress = True
            return r
        except:
            self.task_in_progress = False
            raise StopIteration

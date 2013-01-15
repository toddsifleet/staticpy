from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket


import os
import Queue
import threading

class BulkUploader:
	def __init__(self, aws_keys, bucket, file_filter = None, key_transform = None):
		self.aws_keys = aws_keys
		self.bucket = bucket
		self.key_transform = key_transform
		self.file_filter = file_filter

	def start(self, path):
		self.path = path
		queue = Queue.Queue()
		for (dir_path, dir_name, file_names) in os.walk(path):
			for file_name in file_names:
				file_path = os.path.join(dir_path, file_name)
				if not self.file_filter or self.file_filter(file_path):
					key = self.transform(file_path)
					queue.put((key, file_path))
		threads = []
		for i in range(10):
			thread = Worker(self.aws_keys, self.bucket, queue)
			threads.append(thread)
			thread.start()

		#wait untill everything is done
		queue.join()
		for i in threads:
			i.join()

	def transform(self, path):
		if self.key_transform:
			path = self.key_transform(path)
		path = path[len(self.path)+1::]
		return path.replace('\\', '/')

class Worker(threading.Thread):
	def __init__(self, aws_keys, bucket, queue):
		self.queue = queue
		self.aws_keys = aws_keys
		self.bucket = bucket
		threading.Thread.__init__(self)
		self.daemon = True


	def run(self):
		self.bucket = Bucket(
			connection = S3Connection(*self.aws_keys),
			name = self.bucket
		)
		
		for key, file_path in IterQueue(self.queue):
			self.upload(key, file_path)

	def upload(self, key, file_path):
		s3_key = self.bucket.get_key(key)
		with open(file_path) as fh:
			new_hash, _ = s3_key.compute_md5(fh)
			old_hash = s3_key.etag.strip('"')
			if new_hash == old_hash:
				print "File %s unchanged" % key
			else:
				print "Uploading: %s " % key
				s3_key.set_contents_from_file(fh)

class IterQueue:
	'''Iterate through a Queue.Queue instance

		This allows for easy iteration throught a queue. You don't need
		to worry about setting anything up.  Runs untill the queue is empty

		use:
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
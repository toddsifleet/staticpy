from __future__ import absolute_import

import os
from multiprocessing import Pool

from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from boto.s3.key import Key

from .utils import logger


def transform(path):
    if path.endswith('index.html'):
        return path
    elif path.endswith('.html'):
        return path[0:-5]
    return path


def get_key(base, path):
    path = transform(path)
    path = path[len(base)+1::]
    return path.replace('\\', '/')


def file_filter(file_name):
    return not file_name.startswith('.')


def upload_to_s3(aws_keys, bucket, source_path):
    '''Upload a directory to S3

    Walks a directory uploading everyfile to s3, they S3 key is equivalent to
    the path to the file, less the source_path.

    Note:
        1) Only upload files that differ from what is currently in S3
        2) Delete files from S3 that are not present locally
        3) Use multiprocessing to run upto 10 concurrent uploads

    :param tuple aws_keys: ('access_key', 'secret_key')
    :param str bucket: amazon s3 bucket name
    :param str source_path: Path to the directory to upload
    '''
    current_keys = set()
    pool = Pool(processes=10)
    for (path, _, files) in os.walk(source_path, followlinks=True):
        for file_name in files:
            if file_filter(file_name):
                file_path = os.path.join(path, file_name)
                key = get_key(source_path, file_path)
                current_keys.add(key)
                pool.apply_async(upload, [aws_keys, bucket, key, file_path])
    pool.apply_async(delete_removed_keys, [aws_keys, bucket, current_keys])
    pool.close()
    pool.join()


def delete_removed_keys(aws_keys, bucket, current_keys):
    conn = S3Connection(*aws_keys)
    bucket = conn.get_bucket(bucket)
    old_keys = set([x.name for x in bucket.list()])
    to_delete = old_keys - current_keys
    logger.warning('Deleting {count} files from s3', count=len(to_delete))
    for key in to_delete:
        logger.warning('Deleting `{key}` from S3', key=key)
    bucket.delete_keys(to_delete)


def upload(credentials, bucket, key, file_path):
    bucket = Bucket(
        connection=S3Connection(*credentials),
        name=bucket
    )

    s3_key = bucket.get_key(key)
    if s3_key:
        old_hash = s3_key.etag.strip('"')
    else:
        s3_key = Key(bucket)
        s3_key.key = key
        old_hash = None

    with open(file_path) as fh:
        new_hash, _ = s3_key.compute_md5(fh)
        if new_hash == old_hash:
            logger.info("File {key} unchanged", key=key)
        else:
            s3_key.set_contents_from_file(fh)
            logger.success('Uploaded: {key}', key=key)

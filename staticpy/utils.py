import os
import shutil
import errno

def link_static(site_path, output_path):
    try:
        os.symlink(
            os.path.join(site_path, 'static'),
            os.path.join(output_path, 'static')
        )
    except:
        print '%s/static already exists' % output_path


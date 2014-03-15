import os
import shutil
import errno

def copy_file(file_path, new_file_path):
    #make sure all of the directories leading up to the file exist
    try:
        os.makedirs(new_file_path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    shutil.copy(file_path, new_file_path)

def copy_static(site_path, output_path):
    '''Copy the contents of the static directory from our site_path to our
    output_path.  If /output_path/static already exists we delete it!'''

    static_dir_in = os.path.join(site_path, 'static')
    if not os.path.isdir(static_dir_in):
        print "dir %s not found" % static_dir_in
        return

    static_dir_out = os.path.join(output_path, 'static')
    if os.path.isdir(static_dir_out):
        #not sure if this is good, instead of diffing the directory
        #we just remove the old one and copy everything
        shutil.rmtree(static_dir_out)
    shutil.copytree(static_dir_in, static_dir_out)

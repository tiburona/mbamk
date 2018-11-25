import gzip

from flask import current_app
def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"

def gzip_file(file_path):
    """ Gzip a file
    :param str file_path: path to the file to compress
    :return: two-tuple of the file object and file path
    :rtype: tuple
    """
    with gzip.open(file_path + '.gz', 'wb') as gzipped_file:
        with open(file_path, 'rb') as f:
            gzipped_file.writelines(f)
    return (gzipped_file, file_path + '.gz')



import gzip
import os

from flask import current_app


def debug():
    assert current_app.debug == False, "Don't panic! You're here by request of debug()"


def gzip_file(file_path, delete=False):
    """ Gzip a file
    :param file_path: path to the file to compress
    :type file_path: str
    :param delete: whether to delete the original file after compressing it
    :type delete: bool
    :return: two-tuple of the file object and file path
    :rtype: tuple
    """
    with gzip.open(file_path + '.gz', 'wb') as gzipped_file:
        with open(file_path, 'rb') as f:
            gzipped_file.writelines(f)
    if delete:
        os.remove(file_path)
    return gzipped_file, file_path + '.gz'


def crop(string, pattern, left=True):
    """Crop a string to the section either before or after the index of the beginning of a given pattern

    :param string: the string to search
    :type string: str
    :param pattern: the pattern to match
    :type pattern: str
    :param left: whether to return the string up until the index (left) or the string at and after the index
    :type left: bool
    :return: the cropped strong
    :rtype: str
    """
    index = string.find(pattern)
    if left:
        return string[index:]
    else:
        return string[:pattern]




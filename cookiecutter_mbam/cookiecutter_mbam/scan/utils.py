import gzip

def gzip_file(file, file_name):
    """ Gzip a file
    :param file file:
    :param str file_name:
    :return: the gzipped file
    :rtype: gzip file
    """
    with gzip.open(file_name + '.gz', 'wb') as gzipped_file:
        gzipped_file.writelines(file)
    return gzipped_file



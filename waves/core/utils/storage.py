""" WAVES Files storage engine parameters """

import os

from django.core.files.storage import FileSystemStorage

from waves.settings import waves_settings


class WavesStorage(FileSystemStorage):
    """ Waves FileSystem Storage engine """

    def __init__(self):
        super(WavesStorage, self).__init__(location=waves_settings.DATA_ROOT,
                                           directory_permissions_mode=0o775,
                                           file_permissions_mode=0o775)


class BinaryStorage(FileSystemStorage):
    """ Waves binary file storage engine """

    def __init__(self):
        super(BinaryStorage, self).__init__(location=waves_settings.BINARIES_DIR,
                                            directory_permissions_mode=0o775,
                                            file_permissions_mode=0o775)


def file_sample_directory(instance, filename):
    """ Submission file sample directory upload pattern """
    return os.path.join('sample', str(instance.file_input.submission.service.api_name),
                        str(instance.file_input.submission.slug), filename)


def binary_directory(instance, filename):
    return os.path.join(str(instance.slug), filename)


def job_file_directory(instance, filename):
    """ Submitted job input files """
    return 'jobs/{0}/{1}'.format(str(instance.job.slug), filename)


def allow_display_online(file_name):
    """
    Determine if current 'input' or 'output' may be displayed online, maximum file size is set to '1Mo'
    :param file_name: file name to test for size
    :return: bool
    """
    display_file_online = 1024 * 1024 * 1
    try:
        size = os.path.getsize(file_name)
        return display_file_online >= size > 0
    except os.error:
        return False


waves_storage = WavesStorage()
binary_storage = BinaryStorage()

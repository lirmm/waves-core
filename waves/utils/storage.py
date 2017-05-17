""" WAVES Files storage engine parameters """
from __future__ import unicode_literals

import os

from waves.settings import waves_settings
from django.core.files.storage import FileSystemStorage


class WavesStorage(FileSystemStorage):
    """ Waves FileSystem Storage engine """

    def __init__(self):
        super(WavesStorage, self).__init__(location=waves_settings.DATA_ROOT,
                                           directory_permissions_mode=0o775,
                                           file_permissions_mode=0o775)


def file_sample_directory(instance, filename):
    """ Submission file sample directory upload pattern """
    return 'sample/{0}/{1}/{2}'.format(str(instance.file_input.submission.service.api_name),
                                       str(instance.file_input.submission.slug),
                                       filename)


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
    return False

waves_storage = WavesStorage()

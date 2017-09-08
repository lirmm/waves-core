""" WAVES jobs related web views """
from __future__ import unicode_literals

from waves.wcore.models import JobOutput, JobInput
from waves.wcore.views.files import DownloadFileView


class JobFileView(DownloadFileView):
    """ Extended FileView for job files """

    @property
    def file_description(self):
        raise NotImplementedError()

    context_object_name = "file_obj"

    @property
    def file_name(self):
        return self.object.value

    @property
    def file_path(self):
        return self.object.file_path

    @property
    def return_link(self):
        return self.object.job.get_absolute_url()


class JobOutputView(JobFileView):
    """ Extended JobFileView for job outputs """
    model = JobOutput

    @property
    def file_description(self):
        return self.object.name


class JobInputView(JobFileView):
    """ Extended JobFileView for job inputs """
    model = JobInput

    @property
    def file_description(self):
        return ""

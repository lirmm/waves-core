""" Base class for exporting objects """
from __future__ import unicode_literals

from os.path import join

from django.contrib import messages
from django.shortcuts import redirect
from waves.compat import config

from waves.settings import waves_settings
from waves.models.base import ExportAbleMixin
from waves.views.files import DownloadFileView


class ModelExportView(DownloadFileView):
    """ Enable simple model export with DRF subclasses must declare property method to set up
    serializer used for process
    """
    model = None
    _force_download = True
    serializer = None
    return_view = "admin:index"

    def get_context_data(self, **kwargs):
        assert isinstance(self.object, ExportAbleMixin), 'Model object must be Export-able'
        self.object.serialize()
        context = super(ModelExportView, self).get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        from waves.models.base import ExportError
        try:
            return super(ModelExportView, self).get(request, *args, **kwargs)
        except ExportError as e:
            messages.error(self.request, 'Oops: %s' % e)
            return redirect(self.return_view)

    @property
    def file_path(self):
        return join(config.DATA_ROOT, self.file_name)

    @property
    def file_name(self):
        return self.object.export_file_name

    @property
    def file_description(self):
        return "Export file for %s " % self.model.__class__.__name__


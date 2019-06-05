from __future__ import unicode_literals

import os
from wsgiref.util import FileWrapper

import magic
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
from django.views import generic
from waves.wcore.models.base import ExportAbleMixin


class DownloadFileView(generic.DetailView):
    """ Dedicated view for file, add ?export=1 param to force download """
    template_name = 'waves/services/file.html'
    context_object_name = 'file'
    slug_field = 'slug'
    http_method_names = ['get', ]
    _force_download = True
    file_type = None
    object = None

    def get_object(self, queryset=None):
        """ Retrieve object and validate that it has expected file_path"""
        obj = super(DownloadFileView, self).get_object(queryset)
        if obj is None:
            raise Http404('Object does not exists')
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        assert isinstance(self.object, ExportAbleMixin), 'Model object must be Export-able'
        self.object.serialize()
        self.file_type = magic.from_file(self.file_path)
        export = 'export' in self.request.GET or self._force_download is True
        if 'text' not in self.file_type and not export:
            return HttpResponseRedirect(self.request.path + "?export=1")
        return super(DownloadFileView, self).get(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        """ Creates a response with file asked, otherwise returns displayed file as 'Text'
            template response. """
        # Sniff if we need to return a CSV export
        export = 'export' in self.request.GET or self._force_download is True
        if export:
            wrapper = FileWrapper(open(self.file_path, 'r'))
            response = HttpResponse(wrapper, content_type='application/force-download')
            response['Content-Disposition'] = 'attachment; filename="' + self.file_name + '"'
            response['X-Sendfile'] = smart_str(self.file_path)
            response['Content-Length'] = os.path.getsize(self.file_path)
            return response
        else:
            return super(DownloadFileView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        """ Add file_content / return link / file_description / file_name to context """
        context = super(DownloadFileView, self).get_context_data(**kwargs)
        try:
            if not os.path.isfile(self.file_path):
                raise Http404('File does not exists')
        except AttributeError as e:
            raise Http404('File does not exists %s' % e)
        if 'export' not in self.request.GET:
            if 'text' in self.file_type:
                with open(self.file_path) as fp:
                    context['file_content'] = fp.read()
            else:
                context['file_content'] = "Not Printable data (Human readable)"
            context['return_link'] = self.return_link
            context['file_description'] = self.file_description
            context['file_name'] = self.file_name
        return context

    @property
    def return_link(self):
        """ Return link property, default '#'"""
        return "#"

    @property
    def file_description(self):
        """ Abstract method, must be overridden in child class """
        raise NotImplementedError('file_description function must be defined')

    @property
    def file_name(self):
        """ Abstract method, must be overridden in child class """
        raise NotImplementedError('file_name function must be defined')

    @property
    def file_path(self):
        """ Abstract method, must be overridden in child class """
        raise NotImplementedError('file_path function must be defined')

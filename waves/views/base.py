""" Simple Views for WAVES """
from __future__ import unicode_literals

from django.views import generic

__all__ = ['WavesBaseContextMixin', 'HomePage', 'AboutPage', 'HTML403', 'RestServices']


class WavesBaseContextMixin(generic.base.ContextMixin):
    """ Uses of css_theme in templates """
    def get_context_data(self, **kwargs):
        context = super(WavesBaseContextMixin, self).get_context_data(**kwargs)
        return context


class HomePage(generic.TemplateView, WavesBaseContextMixin):
    """ WAVES home page"""
    template_name = "home.html"


class AboutPage(generic.TemplateView, WavesBaseContextMixin):
    """ WAVES about page """
    template_name = "about.html"


class HTML403(generic.TemplateView, WavesBaseContextMixin):
    """ WAVES 403 page """
    template_name = "403.html"


class RestServices(generic.TemplateView, WavesBaseContextMixin):
    """ REST API service presentation page """
    template_name = "rest/rest_api.html"

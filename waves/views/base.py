""" Simple Views for WAVES """
from __future__ import unicode_literals

from django.views import generic

__all__ = ['WavesBaseContextMixin']


class WavesBaseContextMixin(generic.base.ContextMixin):
    """ Uses of css_theme in templates """
    def get_context_data(self, **kwargs):
        context = super(WavesBaseContextMixin, self).get_context_data(**kwargs)
        return context

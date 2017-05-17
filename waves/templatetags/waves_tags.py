from __future__ import unicode_literals

from django import template

from waves.settings import waves_settings
from waves.models import ServiceCategory

register = template.Library()


@register.inclusion_tag('services/_category_menu.html')
def categories_menu(current):
    """ Setup nodes for left-hand categories menu"""
    categories = ServiceCategory.objects.all()
    return {'nodes': categories, 'current': current}


@register.inclusion_tag('services/_online_execution.html', takes_context=True)
def online_exec_button(context, service, label=None):
    """ for service, setup if current usr can submit jobs """
    return {'available_for_submission': service.available_for_user(context['user']),
            'label': label, 'service': service}


@register.simple_tag
def get_app_version():
    return waves_settings.VERSION

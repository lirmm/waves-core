from __future__ import unicode_literals

from django import template

from waves.core.settings import waves_settings

register = template.Library()


@register.inclusion_tag('waves/services/_online_execution.html', takes_context=True)
def online_exec_button(context, service, label=None):
    """ for service, setup if current usr can submit jobs """
    return {'available_for_submission': service.available_for_user(context['user']) and context.get('preview') is None,
            'label': label, 'service': service}


@register.simple_tag
def get_app_version():
    return waves_settings.VERSION

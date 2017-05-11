from __future__ import unicode_literals

from django import template
import waves.settings
from constance import config
from waves.models import ServiceCategory
register = template.Library()


@register.simple_tag
def get_admin_title():
    """ Returns Admin-Interface title """
    return config.WAVES_ADMIN_TITLE


@register.simple_tag
def get_app_verbose_name():
    """ return current app Verbose name"""
    return config.WAVES_APP_VERBOSE_NAME


@register.simple_tag
def get_app_name():
    """ return current app name """
    return config.WAVES_APP_NAME


@register.inclusion_tag('services/_category_menu.html')
def categories_menu(current):
    """ Setup nodes for left-hand categories menu"""
    categories = ServiceCategory.objects.all()
    return {'nodes': categories, 'current': current}


@register.inclusion_tag('services/_register_for_api.html', takes_context=True)
def register_for_api_button(context, service):
    """ Enable register for waves_api button """
    return {'user': context['user'], 'api_on': service.api_on}


@register.inclusion_tag('services/_online_execution.html', takes_context=True)
def online_exec_button(context, service, label=None):
    """ for service, setup if current usr can submit jobs """
    return {'available_for_submission': service.available_for_user(context['user']),
            'label': label, 'service': service}


@register.simple_tag
def get_app_version():
    return waves.settings.WAVES_VERSION

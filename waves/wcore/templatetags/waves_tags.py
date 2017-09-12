from __future__ import unicode_literals

from django import template

from waves.wcore.settings import waves_settings

register = template.Library()


@register.inclusion_tag('waves/services/_online_execution.html', takes_context=True)
def online_exec_button(context, service, label=None):
    """ for service, setup if current usr can submit jobs """
    return {'available_for_submission': service.available_for_user(context['user']) and context.get('preview') is None,
            'label': label, 'service': service}


@register.simple_tag
def get_app_version():
    return waves_settings.VERSION


@register.inclusion_tag('waves/services/base_inc.html')
def service_inc(inc_type):
    return {'template': "waves/services/" + waves_settings.TEMPLATE_PACK + "/inc." + inc_type + ".html"}


@register.inclusion_tag('waves/services/base_form.html', takes_context=True)
def submission_form(context, template_pack=None):
    tpl_pack = template_pack or waves_settings.TEMPLATE_PACK
    return {'template_form': "waves/services/" + tpl_pack + "/submission_form.html",
            'submissions': context['submissions']}

from __future__ import unicode_literals

from django import template

from waves.core.settings import waves_settings

register = template.Library()


@register.inclusion_tag('waves/services/_online_execution.html', takes_context=True)
def online_exec_button(context, service, label=None):
    """ for service, setup if current usr can submit jobs """
    if service.default_submission:
        return {
            'available_for_submission': service.default_submission.available_for_user(context['user']) and context.get(
                'preview') is None,
            'label': label, 'service': service}
    return {}


@register.simple_tag
def get_app_version():
    from waves.core import __version_detail__, __version__
    return "%s (%s)" % (__version__, __version_detail__)


@register.inclusion_tag('waves/services/forms/service_inc.html')
def service_inc(inc_type):
    return {'template': "waves/services/forms/" + waves_settings.TEMPLATE_PACK + "/inc." + inc_type + ".html"}


@register.inclusion_tag('waves/services/forms/base_form.html', takes_context=True)
def submission_form(context, template_pack=None):
    tpl_pack = template_pack or waves_settings.TEMPLATE_PACK
    return {'template_form': "waves/services/forms/" + tpl_pack + "/submission_form.html",
            'submissions': context['submissions']}

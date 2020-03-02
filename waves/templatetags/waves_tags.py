"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the GNU GPL v3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       https://www.gnu.org/licenses/gpl-3.0.en.html
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from django import template

from waves import __version_detail__, __version__
from waves.settings import waves_settings

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
    return "%s (%s)" % (__version__, __version_detail__)


@register.inclusion_tag('waves/services/forms/service_inc.html')
def service_inc(inc_type):
    return {'template': "waves/services/forms/" + waves_settings.TEMPLATE_PACK + "/inc." + inc_type + ".html"}


@register.inclusion_tag('waves/services/forms/base_form.html', takes_context=True)
def submission_form(context, template_pack=None):
    tpl_pack = template_pack or waves_settings.TEMPLATE_PACK
    return {'template_form': "waves/services/forms/" + tpl_pack + "/submission_form.html",
            'submissions': context['submissions']}

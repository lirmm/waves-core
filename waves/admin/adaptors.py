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
from django.contrib.contenttypes.admin import GenericTabularInline

from waves.models import AdaptorInitParam
from .forms import AdaptorInitParamForm


class AdaptorInitParamInline(GenericTabularInline):
    form = AdaptorInitParamForm
    model = AdaptorInitParam
    extra = 0
    max_num = 0
    fields = ['name', 'value', 'default_value', 'prevent_override']
    readonly_fields = ('name', 'default_value')
    # classes = ('collapse grp-collapse grp-closed',)
    suit_classes = 'suit-tab suit-tab-adaptor'
    # can_delete = False
    verbose_name = 'Execution param'
    verbose_name_plural = "Execution parameters"

    def default_value(self, obj):
        """ Get default values from related adapter concrete class instance """
        init_value = getattr(obj.content_object, 'crypt')
        if init_value is not None:
            return "*" * len(init_value) if init_value is not None else '-'
        if hasattr(init_value, '__iter__'):
            return 'list'
        return init_value if init_value is not None else '-'


class RunnerParamInline(AdaptorInitParamInline):
    """ Job Runner class instantiation parameters insertion field
    Inline are automatically generated from effective implementation class 'init_params' property """
    model = AdaptorInitParam
    can_delete = False
    verbose_name = 'Initialisation parameter'
    verbose_name_plural = "Initialisation parameters"


class ServiceRunnerParamInLine(AdaptorInitParamInline):
    """ adapters parameters for Service """
    model = AdaptorInitParam
    fields = ['name', 'value', ]
    can_delete = False

    def get_queryset(self, request):
        queryset = super(ServiceRunnerParamInLine, self).get_queryset(request)
        queryset = queryset.filter(prevent_override=False)
        return queryset


class SubmissionRunnerParamInLine(ServiceRunnerParamInLine):
    """ Proxy for submission adaptor override """
    pass

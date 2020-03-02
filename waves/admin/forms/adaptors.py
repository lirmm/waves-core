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
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ChoiceField, PasswordInput

from waves.models import AdaptorInitParam, Submission, Service

__all__ = ['AdaptorInitParamForm']


class AdaptorInitParamForm(ModelForm):
    """
    Runner defaults param form
    """

    class Meta:
        """ Metas """
        model = AdaptorInitParam
        fields = ['name', "value", 'prevent_override', 'object_id', 'content_type']

    def __init__(self, **kwargs):
        super(AdaptorInitParamForm, self).__init__(**kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            try:
                from django.utils.module_loading import import_string
                from ast import literal_eval
                concrete = instance.content_object.adaptor
                if concrete is not None:
                    default_value = None
                    initial = instance.value if instance.value else default_value
                    choices = getattr(concrete, instance.name + '_choices', None)
                    if choices:
                        self.fields['value'] = ChoiceField(choices=choices, initial=initial)
                    if not concrete.init_value_editable(instance.name):
                        self.fields['value'].widget.attrs['readonly'] = True
                        if 'prevent_override' in self.fields:
                            self.fields['prevent_override'].widget.attrs['checked'] = True
                            self.fields['prevent_override'].widget.attrs['readonly'] = True
                if instance.name == "password":
                    self.fields['value'].widget = PasswordInput(render_value="",
                                                                attrs={'autocomplete': 'new-password'})
            except ValueError:
                pass

    def clean(self):
        if not self.cleaned_data['value']:
            if isinstance(self.instance.content_object, Submission):
                raise ValidationError({'value': 'Value is mandatory'})
            elif isinstance(self.instance.content_object, Service) \
                    and Submission.objects.filter(runner__isnull=True,
                                                  service=self.instance.content_object).count() > 0:
                raise ValidationError({'value': 'Value is mandatory for forms with no overrides'})

        return super(AdaptorInitParamForm, self).clean()

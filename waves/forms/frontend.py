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
import copy
import logging
from _pydecimal import Decimal

from crispy_forms import bootstrap
from crispy_forms.helper import FormHelper as CrispyFormHelper
from crispy_forms.layout import Layout, Field, Div, HTML, Reset, Submit
from django import forms
from django.core.exceptions import ValidationError

from waves.core.utils import random_analysis_name
from waves.models import FileInput, FileInputSample, Submission, AParam
from waves.settings import waves_settings

logger = logging.getLogger(__name__)


class WFormHelper:

    def __init__(self, *args, **kwargs):
        pass

    def set_layout(self, service_input, form=None):
        raise NotImplementedError()

    def init_layout(self, fields):
        pass

    def end_layout(self):
        pass


class FormHelper(CrispyFormHelper, WFormHelper):
    """
    Extended WFormHelper based on crispy WFormHelper,
    Dynamic form fields according to inputs types and parameters
    """

    # TODO Created dedicated field for (copy_paste field)

    def __init__(self, form=None, **kwargs):
        form_tag = kwargs.pop('form_tag', True)
        form_class = kwargs.pop('form_class', 'form-horizontal')
        label_class = kwargs.pop('label_class', 'col-lg-4')
        field_class = kwargs.pop('field_class', 'col-lg-8 text-left')
        template_pack = kwargs.pop('template_pack', waves_settings.TEMPLATE_PACK)
        self.form_obj = form
        super(FormHelper, self).__init__(form)
        self.form_tag = form_tag
        self.form_class = form_class
        self.label_class = label_class
        self.field_class = field_class
        self.render_unmentioned_fields = False
        self.layout = Layout()
        self.template_pack = template_pack

    def set_layout(self, service_input, form=None):
        """
        Setup crispy form for a submission
        """
        css_class = ""
        field_id = "id_" + service_input.api_name
        dependent_on = ""
        dependent_4_value = ""
        has_sample = isinstance(service_input, FileInput) and service_input.input_samples.count() > 0
        has_dependent = service_input.dependents_inputs.count() > 0

        if has_dependent or has_sample:
            css_class = "has_dependent"

        field_dict = dict(
            css_class=css_class,
            id=field_id,
            title=service_input.help_text,
        )
        wrapper = dict()
        if service_input.parent is not None and not isinstance(service_input, FileInputSample):
            field_id += '_' + service_input.parent.api_name + '_' + service_input.api_name
            dependent_on = service_input.parent.api_name
            dependent_4_value = service_input.when_value
            field_dict.update(dict(dependent_on=service_input.parent.api_name,
                                   dependent_4_value=str(service_input.when_value)))
            when_value = self.form_obj.data.get(service_input.parent.api_name, service_input.parent.default)
            if when_value is None:
                when_value = False
            hide_dep = service_input.when_value_python != when_value
            if when_value is not None:
                if type(service_input.when_value_python) is int:
                    hide_dep = (service_input.when_value_python != int(when_value))
                elif type(service_input.when_value_python) is Decimal:
                    hide_dep = (service_input.when_value_python != Decimal(when_value.strip(' "')))
                elif type(service_input.when_value_python) is bool:
                    bool_value = str(when_value).lower() in ("yes", "true", "t", "1")
                    hide_dep = (service_input.when_value_python != bool_value)

            if hide_dep:
                wrapper = dict(wrapper_class="hid_dep_parameter", disabled="disabled")
            else:
                wrapper = dict(wrapper_class="dis_dep_parameter")
        # file inputs
        if isinstance(service_input, FileInput):
            all_sample = []
            if has_sample:
                for sample in service_input.input_samples.all():
                    all_sample.append(
                        Field('sp_' + service_input.api_name + '_' + str(sample.pk),
                              dependent_on=service_input.api_name,
                              dependent_4_value=dependent_4_value, **wrapper)
                    )
            field_dict.update(wrapper)
            input_field = Div(
                Field(service_input.api_name, **field_dict),
                *all_sample
            )

            if service_input.allow_copy_paste:
                cp_input_field = Field('cp_' + service_input.api_name, css_id='id_' + 'cp_' + service_input.api_name)
                tab_input = bootstrap.Tab(
                    "File Upload",
                    input_field,
                    css_id='tab_' + service_input.api_name
                )
                self.layout.append(
                    Div(
                        bootstrap.TabHolder(
                            tab_input,
                            bootstrap.Tab(
                                "Copy/paste content",
                                cp_input_field,
                                css_class='copypaste',
                                css_id='tab_cp_' + service_input.api_name,
                                dependent_on=dependent_on,
                                dependent_4_value=dependent_4_value,
                            ),
                            css_id='tab_holder_' + service_input.api_name,
                        ),
                        id='tab_pane_' + service_input.api_name,
                        css_class=wrapper['wrapper_class'],
                        dependent_on=dependent_on,
                        dependent_4_value=dependent_4_value
                    )
                )

            else:
                self.layout.append(input_field)
        elif not isinstance(service_input, FileInputSample):
            field_dict.update(wrapper)
            input_field = Field(service_input.api_name, **field_dict)
            self.layout.append(input_field)
        if isinstance(service_input,
                      FileInput) and not service_input.allow_copy_paste and service_input.input_samples.count() > 0:
            for sample in service_input.input_samples.all():
                self.layout.append(Field('sp_' + service_input.api_name + '_' + str(sample.pk)))

    def init_layout(self, fields):
        l_fields = []
        for field in fields:
            l_fields.append(Field(field))
        self.layout = Layout()
        self.layout.extend(l_fields)
        return self.layout

    def end_layout(self):
        self.layout.extend([
            HTML('<HR/>'),
            bootstrap.FormActions(
                Reset('reset', 'Reset form'),
                Submit('save', 'Submit a job')
            )
        ])


class ServiceSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'email']

    slug = forms.CharField(widget=forms.HiddenInput())
    title = forms.CharField(label="Name your analysis", required=True)
    email = forms.EmailField(label="Mail me results", required=False)

    def process_dependent(self, dependent_input):
        # conditional parameters must not be required to use classic django form validation process
        dependent_input.required = False
        logger.warning("current input %s %s ", dependent_input, dependent_input.label)
        self.fields.update(dependent_input.form_widget(self.data.get(dependent_input.api_name, None)))
        self.helper.set_layout(dependent_input)
        for srv_input in dependent_input.dependents_inputs.exclude(required=None):
            self.process_dependent(srv_input)

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        self.user = kwargs.pop('user', None)
        self.form_action = kwargs.pop('form_action', None)
        self.template_pack = kwargs.pop('template_pack', 'bootstrap3')
        self.submit_ajax = kwargs.pop("submit_ajax", False)
        super(ServiceSubmissionForm, self).__init__(*args, **kwargs)
        self.helper = self.get_helper(form_tag=True, template_pack=self.template_pack)
        init_fields = ['title', 'slug']
        if self.instance.service.email_on:
            init_fields.append('email')
        self.fields['title'].initial = 'Job %s' % random_analysis_name()
        self.fields['slug'].initial = str(self.instance.slug)
        self.list_inputs = list(self.instance.expected_inputs.order_by('-required', 'order'))
        self.helper.init_layout(fields=self.fields)

        extra_fields = []
        for service_input in self.list_inputs:
            assert isinstance(service_input, AParam)
            self.fields.update(service_input.form_widget(self.data.get(service_input.api_name, None)))
            self.helper.set_layout(service_input)

            for dependent_input in service_input.dependents_inputs.exclude(required=None):
                self.process_dependent(dependent_input)
        self.list_inputs.extend(extra_fields)
        self.helper.end_layout()
        if self.form_action:
            self.helper.form_action = self.form_action
        if self.submit_ajax:
            self.helper.form_class = self.helper.form_class + ' submit-ajax'

    def get_helper(self, **helper_args):
        # TODO add dynamic Helper class loading
        return FormHelper(form=self, **helper_args)

    def clean(self):
        cleaned_data = super(ServiceSubmissionForm, self).clean()
        for data in copy.copy(cleaned_data):
            srv_input = next((x for x in self.list_inputs if x.name == data), None)
            sample_selected = False
            if srv_input:
                # posted data correspond to a expected input for service
                posted_data = cleaned_data.get(srv_input.name)
                if isinstance(srv_input, FileInput):
                    if srv_input.input_samples.count() > 0:
                        for input_sample in srv_input.input_samples.all():
                            sample_selected = cleaned_data.get('sp_' + srv_input.name + '_' + str(input_sample.pk),
                                                               None)

                            if 'sp_' + srv_input.name in self.cleaned_data:
                                del self.cleaned_data['sp_' + srv_input.name + '_' + str(input_sample.pk)]
                            if sample_selected:
                                sample_selected = input_sample.pk
                                break
                    if not sample_selected:
                        if not cleaned_data.get('cp_' + srv_input.name, False):
                            if srv_input.mandatory and not posted_data:
                                # No posted data in copy/paste but file field is mandatory, so raise error
                                self.add_error(srv_input.name,
                                               ValidationError('You must provide data for %s' % srv_input.label))
                        else:
                            # cp provided, push value in base file field
                            cleaned_data[srv_input.name] = cleaned_data.get('cp_' + srv_input.name)
                    else:
                        cleaned_data[srv_input.name] = sample_selected
                    # Remove all cp_ from posted data
                    if 'cp_' + srv_input.name in self.cleaned_data:
                        del self.cleaned_data['cp_' + srv_input.name]
                else:
                    pass
                    # validator.validate_input(srv_input, posted_data, self)
        return cleaned_data

    def is_valid(self):
        return super(ServiceSubmissionForm, self).is_valid()

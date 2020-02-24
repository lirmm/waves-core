import copy
import logging

from django import forms
from django.core.exceptions import ValidationError

from forms.frontend import FormHelper
from waves.models import Submission
from waves.models import AParam, FileInput
from waves.core.utils import random_analysis_name

logger = logging.getLogger(__name__)


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

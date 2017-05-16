from __future__ import unicode_literals

import copy
import logging

from django import forms
from django.core.exceptions import ValidationError

from waves.compat import config
from waves.forms.lib.crispy import FormHelper
from waves.models.inputs import *
from waves.models.samples import *
from waves.models.submissions import Submission
from waves.utils.validators import ServiceInputValidator

logger = logging.getLogger(__name__)

# TODO refactoring for the copy_paste field associated with FileInput (override formfield template ?)
class ServiceForm(forms.ModelForm):
    pass


class ServiceSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'email']

    slug = forms.CharField(widget=forms.HiddenInput())
    title = forms.CharField(label="Name your analysis", required=True)
    email = forms.EmailField(label="Mail me results", required=False)

    def __init__(self, *args, **kwargs):
        parent_form = kwargs.pop('parent', None)
        super(ServiceSubmissionForm, self).__init__(*args, **kwargs)
        self.helper = self.get_helper(form_tag=True)
        self.helper.init_layout(fields=('title', 'email', 'slug'))
        # Always add "title" / "slug" to submitted jobs
        self.fields['title'].initial = 'my %s job' % self.instance.service.name
        self.fields['slug'].initial = str(self.instance.slug)
        self.list_inputs = list(self.instance.expected_inputs.order_by('-required', 'order'))
        extra_fields = []
        for service_input in self.list_inputs:
            assert isinstance(service_input, AParam)
            self.add_field(service_input)
            if isinstance(service_input, FileInput):
                extra_fields.append(self._create_copy_paste_field(service_input))
                for input_sample in service_input.input_samples.all():
                    self.add_field(input_sample)

            self.helper.set_layout(service_input, self)
            for dependent_input in service_input.dependents_inputs.exclude(required=None):
                # conditional parameters must not be required to use classic django form validation process
                dependent_input.required = False
                logger.warn("current input %s %s ", dependent_input, dependent_input.label)
                if isinstance(dependent_input, FileInput):
                    extra_fields.append(self._create_copy_paste_field(dependent_input))
                    for input_sample in dependent_input.input_samples.all():
                        self.add_field(input_sample)
                self.add_field(dependent_input)
                self.helper.set_layout(dependent_input, self)
        self.list_inputs.extend(extra_fields)
        self.helper.end_layout()

    def add_field(self, service_input):
        field_dict = dict(
            label=service_input.label,
            required=service_input.required,
            help_text=service_input.help_text,
            initial=self.data.get(service_input.name) or service_input.default
        )
        field_name = service_input.name
        if isinstance(service_input, FileInput):
            field_dict.update(dict(allow_empty_file=False, required=False))
            form_field = forms.FileField(**field_dict)
        elif isinstance(service_input, BooleanParam):
            field_dict.update(dict(initial=(service_input.default == service_input.true_value)))
            form_field = forms.BooleanField(**field_dict)
        elif isinstance(service_input, ListParam):
            field_dict.update(dict(choices=service_input.choices))
            if not service_input.multiple:
                form_field = forms.ChoiceField(**field_dict)
                if service_input.list_mode == ListParam.DISPLAY_RADIO:
                    form_field.widget = forms.RadioSelect()
            else:
                form_field = forms.MultipleChoiceField(**field_dict)
                if service_input.list_mode == ListParam.DISPLAY_CHECKBOX:
                    form_field.widget = forms.CheckboxSelectMultiple()
            form_field.css_class = 'text-left'
        elif isinstance(service_input, NumberParam):
            field_dict.update(dict(min_value=service_input.min_val,
                                   max_value=service_input.max_val,))
            if isinstance(service_input, IntegerParam):
                form_field = forms.IntegerField(**field_dict)
            else:
                form_field = forms.DecimalField(**field_dict)
            form_field.widget.attrs['step'] = service_input.step
        elif isinstance(service_input, FileInputSample):
            form_field = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'no-switch'}), **field_dict)
            field_name = 'sp_%s_%s' % (service_input.file_input.name, service_input.pk)
        else:
            form_field = forms.CharField(**field_dict)
        self.fields[field_name] = form_field

    @staticmethod
    def get_helper(**kwargs):
        return FormHelper(**kwargs)

    def _create_copy_paste_field(self, service_input):
        # service_input.mandatory = False # Field is validated in clean process
        cp_service = copy.copy(service_input)
        cp_service.label = 'Copy/paste content'
        cp_service.description = ''
        cp_service.required = False
        cp_service.name = 'cp_' + service_input.name
        self.add_field(cp_service)
        self.fields[cp_service.name].widget = forms.Textarea(attrs={'cols': 20, 'rows': 10})
        self.fields[cp_service.name].label = False
        return cp_service

    def _create_sample_fields(self, service_input):
        extra_fields = []
        if service_input.input_samples.count() > 0:
            for input_sample in service_input.input_samples.all():
                # sample_field = forms.ChoiceField()
                """
                sample_field.label = "Sample: " + input_sample.name
                sample_field.value = input_sample.file.name
                sample_field.name = 'sp_' + service_input.name + '_' + str(input_sample.pk)
                sample_field.description = ''
                sample_field.required = False
                extra_fields.append(sample_field)
                """
                self.helper.add_field(input_sample, self)
                self.fields['sp_' + service_input.name + '_' + str(input_sample.pk)].initial = False
        return extra_fields

    def clean(self):
        cleaned_data = super(ServiceSubmissionForm, self).clean()
        validator = ServiceInputValidator()
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

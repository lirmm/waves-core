"""
WAVES Service models forms
"""
from __future__ import unicode_literals

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from constance import config
import waves.settings
from waves.models.inputs import *
from waves.models.submissions import Submission
from waves.models.services import Service, ServiceCategory
from waves.models.runners import Runner
from waves.models.metas import ServiceMeta


__all__ = ['ServiceForm', 'ImportForm', 'ServiceMetaForm', 'SubmissionInlineForm',
           'SubmissionForm']


class SubmissionInlineForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ['name', 'availability', 'api_name']

    def __init__(self, *args, **kwargs):
        super(SubmissionInlineForm, self).__init__(*args, **kwargs)


class ImportForm(forms.Form):
    """
    Service Import Form
    """
    category = forms.ModelChoiceField(label='Import to category',
                                      queryset=ServiceCategory.objects.all())
    tool = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        tool_list = kwargs.pop('tool', ())
        selected = kwargs.pop('selected', None)
        super(ImportForm, self).__init__(*args, **kwargs)
        self.fields['tool'] = forms.ChoiceField(
            choices=tool_list,
            initial=selected,
            disabled=('disabled' if selected is not None else ''),
            widget=forms.widgets.Select(attrs={'size': '15', 'style': 'width:100%; height: auto;'}))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.render_unmentioned_fields = False
        self.helper.form_show_labels = True
        self.helper.form_show_errors = True
        self.helper.layout = Layout(
            Field('category'),
            Field('tool'),
        )
        self.helper.disable_csrf = True


class ServiceForm(forms.ModelForm):
    """
    Service form parameters
    """

    class Meta:
        model = Service
        fields = '__all__'
        widgets = {
            'edam_topics': forms.TextInput(attrs={'size': 50}),
            'edam_operations': forms.TextInput(attrs={'size': 50}),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields['restricted_client'].label = "Restrict access to specified user"
        self.fields['runner'].required = False
        if not self.fields['created_by'].initial:
            self.fields['created_by'].initial = self.current_user
        if not config.WAVES_NOTIFY_RESULTS:
            self.fields['email_on'].widget.attrs['disabled'] = 'disabled'
            self.fields['email_on'].help_text = '<span class="warning">Disabled by main configuration</span><br/>' \
                                                + self.fields['email_on'].help_text

    def clean_email_on(self):
        if not config.WAVES_NOTIFY_RESULTS:
            return self.instance.email_on
        else:
            return self.cleaned_data.get('email_on')


class SampleDepForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SampleDepForm, self).__init__(*args, **kwargs)
        self.fields['related_to'].widget.can_delete_related = False
        self.fields['related_to'].widget.can_add_related = False
        self.fields['related_to'].widget.can_change_related = False


class InputInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InputInlineForm, self).__init__(*args, **kwargs)
        if isinstance(self.instance, ListParam) or isinstance(self.instance, BooleanParam):
            self.fields['default'] = forms.ChoiceField(choices=self.instance.choices, initial=self.instance.default)
            self.fields['default'].required = False
        elif isinstance(self.instance, FileInput):
            self.fields['default'].widget.attrs['style'] = 'display:none'
        if self.instance.parent is not None:
            self.fields['required'].widget.attrs['disabled'] = 'disabled'
            self.fields['required'].widget.attrs['title'] = 'Inputs with dependencies must be optional'


class TextParamForm(forms.ModelForm):
    class Meta:
        model = TextParam
        exclude = ['order']


class InputSampleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InputSampleForm, self).__init__(*args, **kwargs)
        self.fields['file_input'].widget.can_delete_related = False
        self.fields['file_input'].widget.can_add_related = False
        self.fields['file_input'].widget.can_change_related = False


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        exclude = ['order']

    runner = forms.ModelChoiceField(queryset=Runner.objects.all(), empty_label="Use Service Config")


class ServiceMetaForm(forms.ModelForm):
    class Meta:
        model = ServiceMeta
        exclude = ['order']

    def clean(self):
        cleaned_data = super(ServiceMetaForm, self).clean()
        try:
            validator = validators.URLValidator()
            validator(cleaned_data['value'])
            self.instance.is_url = True
        except ValidationError as e:
            if self.instance.type in (self.instance.META_WEBSITE, self.instance.META_DOC, self.instance.META_DOWNLOAD):
                raise e


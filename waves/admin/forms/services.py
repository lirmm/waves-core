"""
WAVES Service models forms
"""

from django import forms
from django.conf import settings

from waves.settings import waves_settings as config
from waves.models import Service, Submission
from waves.models.inputs import ListParam, AParam, BooleanParam, FileInput, \
    FileInputSample
from waves.models.runners import Runner
from waves.models.services import SubmissionOutput, SubmissionExitCode

__all__ = ['ServiceForm', 'ImportForm', 'SubmissionInlineForm', 'InputInlineForm', 'SubmissionExitCodeForm',
           'SubmissionOutputForm', 'SampleDepForm', 'InputSampleForm', 'SampleDepForm2',
           'ServiceSubmissionForm']


class SubmissionInlineForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['name', 'availability', 'api_name']

    def __init__(self, *args, **kwargs):
        super(SubmissionInlineForm, self).__init__(*args, **kwargs)

    runner = forms.ModelChoiceField(queryset=Runner.objects.all(),
                                    required=False,
                                    empty_label="----- use service configuration -----",
                                    help_text="Changing value need more configuration")


class ImportForm(forms.Form):
    class Meta:
        model = Runner
        fields = ('name', 'running_services', 'tool')
        # fields = ('name', 'tool')

    """
    Service Import Form
    """
    running_services = forms.ChoiceField()
    tool = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(ImportForm, self).__init__(*args, **kwargs)
        list_service = [(x.pk, x.name) for x in self.instance.running_services]
        list_service.insert(0, (None, 'Create new service'))
        self.fields['tool'] = forms.ChoiceField(
            choices=self.instance.importer.list_services(),
            widget=forms.widgets.Select(attrs={'size': '15', 'style': 'width:100%; height: auto;'}),
            label="Available tools",
            help_text="")
        self.fields['running_services'] = forms.ChoiceField(
            choices=list_service,
            required=False,
            label="Create submission for service")


class ServiceSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = '__all__'

    @property
    def media(self):
        if 'jet' in settings.INSTALLED_APPS:
            js = ('waves/admin/js/submission_jet.js',)
        else:
            js = ('waves/admin/js/submissions.js',)
        return forms.Media(js=js)

    runner = forms.ModelChoiceField(queryset=Runner.objects.all(), empty_label="----- use service configuration -----")


class ServiceForm(forms.ModelForm):
    """
    Service form parameters
    """

    class Meta:
        model = Service
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields['restricted_client'].label = "Restrict access to specified user"
        if 'created_by' in self.fields and not self.fields['created_by'].initial:
            self.fields['created_by'].initial = self.current_user
        if not config.NOTIFY_RESULTS:
            self.fields['email_on'].widget.attrs['disabled'] = 'disabled'
            self.fields['email_on'].help_text = '<span class="warning">Disabled by main configuration</span><br/>' \
                                                + self.fields['email_on'].help_text

    def clean_email_on(self):
        if not config.NOTIFY_RESULTS:
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
        if isinstance(self.instance, FileInput):
            self.fields['default'].widget.attrs['readonly'] = True
        if self.instance.parent is not None:
            self.fields['required'].widget.attrs['disabled'] = 'disabled'
            self.fields['required'].widget.attrs['title'] = 'Inputs with dependencies must be optional'


class InputSampleForm(forms.ModelForm):
    class Meta:
        model = FileInputSample
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(InputSampleForm, self).__init__(*args, **kwargs)
        self.fields['file_input'].widget.can_delete_related = False
        self.fields['file_input'].widget.can_add_related = False
        self.fields['file_input'].widget.can_change_related = False


class InputSampleModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '(%s - %s) %s' % (obj.submission.service.name, obj.submission.name, obj)


def get_related_to():
    return AParam.objects.not_instance_of(FileInput)


class SampleDepForm2(forms.ModelForm):
    related_to = InputSampleModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(SampleDepForm2, self).__init__(*args, **kwargs)
        self.fields['related_to'].queryset = AParam.objects.not_instance_of(FileInput)
        self.fields['file_input'].widget.can_delete_related = False
        self.fields['file_input'].widget.can_add_related = False
        self.fields['file_input'].widget.can_change_related = False
        self.fields['related_to'].widget.can_delete_related = False
        self.fields['related_to'].widget.can_add_related = False
        self.fields['related_to'].widget.can_change_related = False


class SubmissionOutputForm(forms.ModelForm):
    class Meta:
        model = SubmissionOutput
        fields = '__all__'

    def clean(self):
        cleaned_data = super(SubmissionOutputForm, self).clean()
        pattern = cleaned_data.get('file_pattern', None)
        from_input = cleaned_data.get('from_input', None)
        if pattern and '%s' in pattern:
            if from_input is None:
                raise forms.ValidationError('If setting a file pattern, you must choose a source input')


class SubmissionExitCodeForm(forms.ModelForm):
    class Meta:
        model = SubmissionExitCode
        fields = '__all__'

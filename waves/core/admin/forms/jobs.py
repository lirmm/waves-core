from __future__ import unicode_literals
from django import forms
from django.forms import widgets
from waves.core.models import JobInput, JobOutput, Job
__all__ = ['JobInputForm', 'JobOutputForm', 'JobForm']


class ReadOnlyForm(forms.ModelForm):
    """Base class for making a form readonly."""
    def __init__(self, *args, **kwargs):
        super(ReadOnlyForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            if isinstance(self.fields[f].widget, widgets.Select):
                self.fields[f].widget.attrs['disabled'] = 'disabled'
            else:
                self.fields[f].widget.attrs['readonly'] = 'readonly'


class JobInputForm(forms.ModelForm):
    class Meta:
        model = JobInput
        fields = ['value']
        widgets = {
            'input': widgets.Select(attrs={'readonly': True}),
            'value': forms.Textarea(attrs={'rows': 2, 'class': 'span12'})
        }

    def clean(self):
        cleaned_data = super(JobInputForm, self).clean()
        return cleaned_data


class JobOutputForm(ReadOnlyForm):
    class Meta:
        model = JobOutput
        fields = ['value']
        widgets = {
            'value': forms.Textarea(attrs={'rows': 2, 'class': 'span12'})
        }

    def get_file_path(self, object):
        return object.file_path


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'submission', '_status', 'client', 'email_to']
        widgets = {
            'service': widgets.Select(attrs={'disabled': 'disabled'}),
            'client': widgets.Select(attrs={'disabled': 'disabled'})
        }


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
from django import forms
from django.forms import widgets

from waves.models import JobInput, JobOutput, Job

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

    def get_file_path(self, obj):
        return obj.file_path


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'submission', '_status', 'client', 'email_to']
        widgets = {
            'service': widgets.Select(attrs={'disabled': 'disabled'}),
            'client': widgets.Select(attrs={'disabled': 'disabled'}),
        }

"""
Runner configuration BackOffice Forms
"""
from __future__ import unicode_literals

from django.forms import ModelForm, CheckboxInput, BooleanField, ChoiceField, HiddenInput
from django.utils.functional import lazy
from waves.models import Runner
from waves.utils.runners import runner_list

__all__ = ['RunnerForm']


class RunnerForm(ModelForm):
    """ Form to edit a runner
    """
    class Meta:
        """ Metas """
        model = Runner
        exclude = ['id']

    class Media:
        """ Medias """
        js = ('waves/admin/js/runner.js',
              'waves/admin/js/connect.js')

    update_init_params = BooleanField(required=False, label='Reset related services')

    def __init__(self, *args, **kwargs):
        super(RunnerForm, self).__init__(*args, **kwargs)
        self.fields['clazz'] = ChoiceField(label="Run on", choices=runner_list)
        if self.instance.pk is None:
            self.fields['update_init_params'].widget = HiddenInput()
            self.fields['update_init_params'].initial = False

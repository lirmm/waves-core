"""
Runner configuration BackOffice Forms
"""
from __future__ import unicode_literals

from django.forms import ModelForm, CheckboxInput, BooleanField, ChoiceField, HiddenInput
from waves.wcore.models import Runner

__all__ = ['RunnerForm']


def get_runners_list():
    """
    Retrieve enabled waves.wcore.adaptors list from waves settings env file
    :return: a list of Tuple 'value'/'label'
    """
    from waves.wcore.adaptors.loader import AdaptorLoader
    adaptors = AdaptorLoader.get_adaptors()
    grp_impls = {'': 'Select a environment...'}
    for adaptor in adaptors:
        grp_name = adaptor.__class__.__module__.split('.')[-1].capitalize()
        if grp_name not in grp_impls:
            grp_impls[grp_name] = []
        grp_impls[grp_name].append((adaptor.__module__ + '.' + adaptor.__class__.__name__, adaptor.__class__.__name__))
    return sorted((grp_key, grp_val) for grp_key, grp_val in grp_impls.items())


class RunnerForm(ModelForm):
    """ Form to edit a runner
    """
    class Meta:
        """ Metas """
        model = Runner
        exclude = ['id']

    class Media:
        """ Medias """
        js = ('admin/waves/js/runner.js',
              'admin/waves/js/connect.js')

    update_init_params = BooleanField(required=False, label='Reset related services')

    def __init__(self, *args, **kwargs):
        super(RunnerForm, self).__init__(*args, **kwargs)
        self.fields['clazz'] = ChoiceField(label="Run on", choices=get_runners_list)
        if self.instance.pk is None:
            self.fields['update_init_params'].widget = HiddenInput()
            self.fields['update_init_params'].initial = False

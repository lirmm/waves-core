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

from django.forms import ModelForm, BooleanField, ChoiceField, HiddenInput

from waves.models import Runner

__all__ = ['RunnerForm']


def get_runners_list():
    """
    Retrieve enabled waves.core.adapters list from waves settings env file
    :return: a list of Tuple 'value'/'label'
    """
    from waves.core.loader import AdaptorLoader
    adaptors = AdaptorLoader.get_adaptors()
    grp_impls = {'': 'Select a environment...'}
    for adaptor in adaptors:
        grp_name = adaptor.__class__.__module__.split('.')[-1].capitalize()
        if grp_name not in grp_impls:
            grp_impls[grp_name] = []
        grp_impls[grp_name].append((adaptor.__module__ + '.' + adaptor.__class__.__name__, adaptor.__class__.name))
    return sorted((grp_key, grp_val) for grp_key, grp_val in grp_impls.items())


class RunnerForm(ModelForm):
    """ Form to edit a runner
    """

    class Meta:
        """ Metas """
        model = Runner
        exclude = ['id']

    # noinspection PyClassHasNoInit
    class Media:
        """ Medias """
        js = ('waves/admin/js/runner.js',
              'waves/admin/js/connect.js')

    update_init_params = BooleanField(required=False, label='Reset related services')

    def __init__(self, *args, **kwargs):
        super(RunnerForm, self).__init__(*args, **kwargs)
        self.fields['clazz'] = ChoiceField(label="Run on", choices=get_runners_list)
        if not self.instance.pk:
            self.fields['update_init_params'].widget = HiddenInput()
            self.fields['update_init_params'].initial = False

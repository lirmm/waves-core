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

from itertools import chain

from django.db import models
from django.urls import reverse

from .adaptors import HasAdaptorClazzMixin
from .base import Described, ExportAbleMixin

__all__ = ['Runner']


class Runner(Described, ExportAbleMixin, HasAdaptorClazzMixin):
    """ Represents a generic job adapter meta information (resolved at runtime via clazz attribute) """

    class Meta:
        ordering = ['name']
        verbose_name = 'Computing infrastructure'
        verbose_name_plural = "Computing infrastructures"
        db_table = 'wcore_runner'
        app_label = "waves"

    name = models.CharField('Label', max_length=50, null=False, help_text='Displayed name')
    enabled = models.BooleanField('Enabled', default=True, null=False, blank=True,
                                  help_text="Runner is enable for job runs")

    @property
    def importer(self):
        """
        Return an Service adapterImporter instance, using either

        :return: an Importer new instance
        """
        if self.adaptor is not None:
            importer = self.adaptor.importer
            importer._runner = self
            return importer
        else:
            return None

    def __str__(self):
        return self.name

    @property
    def serializer(self, context=None):
        """ Retrieve a serializer for json export """
        from waves.core.import_export.runners import RunnerSerializer
        return RunnerSerializer

    def runs(self):
        services_list = self.running_services().all()
        submissions_list = self.running_submissions().all()
        runs_list = list(chain(services_list, submissions_list))
        return runs_list

    def running_services(self):
        from waves.models import Service
        return Service.objects.filter(runner=self)

    def running_submissions(self):
        from waves.models import Submission
        return Submission.objects.filter(runner=self)

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.pk])

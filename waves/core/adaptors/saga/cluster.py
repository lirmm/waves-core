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
from .shell import SshKeyShellAdaptor, SshShellAdaptor
from .base import SagaAdaptor


class LocalClusterAdaptor(SagaAdaptor):
    """
    Encapsulate some of radical-saga adapters for common cluster calculation devices onto WAVES adapter logic
    """
    NOT_AVAILABLE_MESSAGE = "A valid local %s cluster is needed to use this adaptor"

    name = 'Local cluster'
    protocol_choices = (
        ('sge', 'Sun Grid Engine'),
        ('slurm', 'SLURM'),
        ('pbs', 'PBS'),
        ('condor', 'CONDOR'),
        ('pbspro', 'PBS Pro'),
        ('lsf', 'LSF'),
        ('torque', 'TORQUE')
    )
    protocol_default = "sge"

    def __init__(self, command=None, protocol='sge', host="localhost", queue='', **kwargs):
        super(LocalClusterAdaptor, self).__init__(command, protocol, host, **kwargs)
        self.queue = queue

    @property
    def init_params(self):
        """ Base init_params for Cluster JobAdapter """
        base = super(LocalClusterAdaptor, self).init_params
        base.update(dict(queue=self.queue))
        return base

    def _job_description(self, job):
        jd = super(LocalClusterAdaptor, self)._job_description(job)
        jd.update(dict(queue=self.queue))
        return jd


class SshClusterAdaptor(LocalClusterAdaptor, SshShellAdaptor):
    """
    Cluster calls over SSH with user password
    """
    name = 'Cluster over SSH (user/pass)'
    pass




class SshKeyClusterAdaptor(LocalClusterAdaptor, SshKeyShellAdaptor):
    """
    Cluster calls over SSH with private key and pass phrase
    """
    name = 'Cluster over SSH (key)'
    pass

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
import logging
from os.path import join

import radical.saga as rs

from waves.core.exceptions import AdaptorJobException
from .base import SagaAdaptor

logger = logging.getLogger(__name__)


class LocalShellAdaptor(SagaAdaptor):
    """
    Local script job adapter, command line tools must be in path or specified as absolute path
    """
    name = "Local script"
    #: Saga-python protocol scheme
    protocol = 'fork'
    protocol_default = 'fork'

    def __init__(self, command=None, protocol='fork', host="localhost", **kwargs):
        super(LocalShellAdaptor, self).__init__(command, protocol, host, **kwargs)


class SshShellAdaptor(LocalShellAdaptor):
    """
    Saga-python base SSH adapter (Shell remote calls)
    Run locally on remote host job command
    """
    name = 'Shell script over SSH (user/pass)'

    _session = None

    def _disconnect(self):
        super(SshShellAdaptor, self)._disconnect()
        del self._session

    def __init__(self, command=None, protocol='ssh', host="localhost", port=22, password=None, user_id=None,
                 basedir="$HOME/", **kwargs):
        super(SshShellAdaptor, self).__init__(command=command, protocol=protocol, host=host, **kwargs)
        self.user_id = user_id
        self.password = password
        self.port = port
        self.basedir = basedir
        self._context = None
        self._session = None

    def _init_service(self):
        return rs.job.Service(self.saga_host, self.session)

    @property
    def saga_host(self):
        """ Construct saga-python host scheme str """
        if self.protocol != 'ssh':
            saga_host = '%s+ssh://%s' % (self.protocol, self.host)
        else:
            saga_host = super(SshShellAdaptor, self).saga_host
        return '%s:%s' % (saga_host, self.port)

    @property
    def init_params(self):
        """ SSH saga-python required init parameters """
        params = super(SshShellAdaptor, self).init_params
        params.update(dict(user_id=self.user_id,
                           port=self.port,
                           basedir=self.basedir,
                           password=self.password))
        return params

    def _job_description(self, job):
        """
        Job description for saga-python library

        :param job:
        :return: a dictionary with data set up according to job
        """
        desc = super(SshShellAdaptor, self)._job_description(job)
        desc.update(dict(working_directory=self.job_work_dir(job).get_url().path))
        return desc

    @property
    def remote_dir(self):
        """ Construct remote ssh host remote dir (uploads) """
        return "sftp://%s%s" % (self.host, self.basedir)

    @property
    def context(self):
        """ Configure SSH saga context properties """
        if self._context is None:
            self._context = rs.Context('UserPass')
            self._context.user_id = self.user_id
            self._context.user_pass = self.password
            self._context.remote_port = self.port
            self._context.life_time = 0
        return self._context

    def job_work_dir(self, job, mode=rs.filesystem.READ):
        """ Setup remote host working dir """
        return rs.filesystem.Directory(rs.Url('%s/%s' % (self.remote_dir, str(job.slug))), mode,
                                         session=self.session)

    def _prepare_job(self, job):
        """
        Prepare job on remote host
          - Create remote working dir
          - Upload job input files
        """
        job.logger.debug('Prepared job in ShellAdapter')
        try:
            work_dir = self.job_work_dir(job, rs.filesystem.CREATE_PARENTS)
            for input_file in job.input_files:
                wrapper = rs.filesystem.File(
                    rs.Url('file://localhost/%s' % join(job.working_dir, input_file.value)))
                wrapper.copy(work_dir.get_url())
                job.logger.debug("Uploaded file %s to %s", join(job.working_dir, input_file.value), work_dir.get_url())
            return job
        except rs.SagaException as exc:
            raise AdaptorJobException(exc.message)

    def _job_results(self, job):
        """
        Download all files located in remote job working dir

        :param job: the Job to retrieve file for
        :return: None
        """
        try:
            work_dir = self.job_work_dir(job)
            for remote_file in work_dir.list('*'):
                work_dir.copy(remote_file, 'file://localhost/%s/' % job.working_dir)
                job.logger.debug("Retrieved file from %s to %s", remote_file, job.working_dir)
            return super(SshShellAdaptor, self)._job_results(job)
        except rs.SagaException as exc:
            raise AdaptorJobException(exc.message)


class SshKeyShellAdaptor(SshShellAdaptor):
    """
    SSH remote job control, over ssh, authenticated with private key and pass phrase
    """
    name = 'Shell script over SSH (private key)'
    private_key = '$HOME/.ssh/id_rsa'
    public_key = '$HOME/.ssh/id_rsa.pub'

    def __init__(self, command=None, protocol='ssh', host="localhost", port=22, password=None, user_id=None,
                 basedir="$HOME/", **kwargs):
        super(SshKeyShellAdaptor, self).__init__(command, protocol, host, port, password, user_id, basedir, **kwargs)
        self.private_key = kwargs.get('public_key', SshKeyShellAdaptor.private_key)
        self.public_key = kwargs.get('public_key', SshKeyShellAdaptor.public_key)

    @property
    def init_params(self):
        """ Update init params with expected ones from SSH private/public key login """
        params = super(SshKeyShellAdaptor, self).init_params
        params.update(dict(private_key=self.private_key,
                           public_key=self.public_key))
        return params

    @property
    def context(self):
        """ Setup saga context to connect over ssh using private/public key with pass phrase """
        if self._context is None:
            self._context = super(SshKeyShellAdaptor, self).context
            self._context.user_cert = self.private_key
            self._context.user_key = self.public_key
        return self._context

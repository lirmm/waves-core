from __future__ import unicode_literals

import saga
import logging
from os.path import join

import waves.adaptors.const
from waves.adaptors.core.adaptor import JobAdaptor, JobRunDetails
from waves.adaptors.exceptions import *
from waves.utils.encrypt import Encrypt

logger = logging.getLogger(__name__)


class LocalShellAdaptor(JobAdaptor):
    """
    Local script job adaptor, command line tools must be in path or specified as absolute path
    """
    name = "Local script"
    #: Saga-python protocol scheme
    protocol = 'fork'
    protocol_default = 'fork'

    _states_map = {
        saga.job.UNKNOWN: waves.adaptors.const.JOB_UNDEFINED,
        saga.job.NEW: waves.adaptors.const.JOB_QUEUED,
        saga.job.PENDING: waves.adaptors.const.JOB_QUEUED,
        saga.job.RUNNING: waves.adaptors.const.JOB_RUNNING,
        saga.job.SUSPENDED: waves.adaptors.const.JOB_SUSPENDED,
        saga.job.CANCELED: waves.adaptors.const.JOB_CANCELLED,
        saga.job.DONE: waves.adaptors.const.JOB_COMPLETED,
        saga.job.FAILED: waves.adaptors.const.JOB_ERROR,
    }

    def __init__(self, command=None, protocol='fork', host="localhost", **kwargs):
        super(LocalShellAdaptor, self).__init__(command, protocol, host, **kwargs)
        self._session = None

    @property
    def session(self):
        if not self._session:
            session = saga.Session()
            session.add_context(self.context)
            logger.info("New session [--%s--]" % session)
            self._session = session
        return self._session

    @property
    def available(self):
        try:
            service = self._init_service()
        except saga.NoSuccess as e:
            raise AdaptorNotAvailableException(e.message)
        return service.valid

    def init_value_editable(self, init_param):
        if init_param == 'protocol':
            return False
        return super(LocalShellAdaptor, self).init_value_editable(init_param)

    def connexion_string(self):
        return self.saga_host

    @property
    def saga_host(self):
        """ Construct Saga-python adaptor uri scheme """
        return '%s://%s' % (self.protocol, self.host)

    def _init_service(self):
        return saga.job.Service(self.saga_host)

    @property
    def context(self):
        """ Create / initialize Saga-python session context """
        return self._context

    def _connect(self):
        try:
            logger.debug('Connection to %s', self.saga_host)
            self.connector = self._init_service()
            self._connected = self.connector is not None and self.connector.valid and self.connector.session is not None
        except saga.SagaException as exc:
            self._connected = False
            # logger.exception(exc.message)
            raise AdaptorConnectException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

    def job_work_dir(self, job, mode=saga.filesystem.READ):
        return job.working_dir

    def _job_description(self, job):
        desc = dict(working_directory=job.working_dir,
                    executable=self.command,
                    arguments=job.command_line,
                    output=job.stdout,
                    error=job.stderr)
        return desc

    def _disconnect(self):
        logger.debug('Disconnect')
        self.connector.close()
        self.connector = None
        self._connected = False
        self._context = None

    def _prepare_job(self, job):
        # Nothing to do here
        logger.debug('Nothing to prepare, we are local')
        return job

    def _run_job(self, job):
        """
        Launch the job with current parameters from associated history
        Args:
            job:
        """
        try:
            logger.debug('Creating job descriptor')
            jd_dict = self._job_description(job)
            jd = saga.job.Description()
            for key in jd_dict.keys():
                setattr(jd, key, jd_dict[key])
            new_job = self.connector.create_job(jd)
            new_job.run()
            logger.debug('Job Descriptor %s', jd)
            job.remote_job_id = new_job.id
            logger.debug('New saga job %s ', new_job)
            return job
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

    def _cancel_job(self, job):
        """
        Jobs Cancel if connector is available
        """
        try:
            the_job = self.connector.get_job(str(job.remote_job_id))
            the_job.cancel()
            return job
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

    def _job_status(self, job):
        try:
            the_job = self.connector.get_job(str(job.remote_job_id))
            return the_job.state
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

    def _job_results(self, job):
        try:
            saga_job = self.connector.get_job(str(job.remote_job_id))
            job.results_available = True
            job.exit_code = saga_job.exit_code
            return job
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

    def _job_run_details(self, job):
        remote_job = self.connector.get_job(str(job.remote_job_id))
        details = JobRunDetails(job.id, str(job.slug), remote_job.id, remote_job.name,
                                remote_job.exit_code,
                                remote_job.created, remote_job.started, remote_job.finished,
                                remote_job.execution_hosts)
        return details


class SshShellAdaptor(LocalShellAdaptor):
    """
    Saga-python base SSH adaptor (Shell remote calls)
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
        return saga.job.Service(self.saga_host, self.session)

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
            self._context = saga.Context('UserPass')
            self._context.user_id = self.user_id
            self._context.user_pass = Encrypt.decrypt(self.password)
            self._context.remote_port = self.port
            self._context.life_time = 0
        return self._context

    def job_work_dir(self, job, mode=saga.filesystem.READ):
        """ Setup remote host working dir """
        return saga.filesystem.Directory(saga.Url('%s/%s' % (self.remote_dir, str(job.slug))), mode,
                                         session=self.session)

    def _prepare_job(self, job):
        """
        Prepare job on remote host
          - Create remote working dir
          - Upload job input files
        """
        try:
            work_dir = self.job_work_dir(job, saga.filesystem.CREATE_PARENTS)
            for input_file in job.input_files:
                wrapper = saga.filesystem.File(
                    saga.Url('file://localhost/%s' % join(job.working_dir, input_file.value)))
                wrapper.copy(work_dir.get_url())
                logger.debug("Uploaded file %s to %s", join(job.working_dir, input_file.value), work_dir.get_url())
            return job
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)

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
                logger.debug("Retrieved file from %s/%s to %s", work_dir.name, remote_file,
                             'file://localhost/%s/' % job.working_dir)
            return super(SshShellAdaptor, self)._job_results(job)
        except saga.SagaException as exc:
            raise AdaptorJobException(msg='%s: %s' % (exc.type, exc.message.split(':')[0]), parent=exc)


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

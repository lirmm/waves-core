import logging

import radical.saga as rs

from waves.adaptors import exceptions
from waves.adaptors.base import JobAdaptor
from waves.adaptors.const import JobStatus, JobRunDetails

logger = logging.getLogger(__name__)


class SagaAdaptor(JobAdaptor):
    """
    Main Saga-python WAVES adapter container

    """
    _session = None
    _states_map = {
        rs.job.UNKNOWN: JobStatus.JOB_UNDEFINED,
        rs.job.NEW: JobStatus.JOB_QUEUED,
        rs.job.PENDING: JobStatus.JOB_QUEUED,
        rs.job.RUNNING: JobStatus.JOB_RUNNING,
        rs.job.SUSPENDED: JobStatus.JOB_SUSPENDED,
        rs.job.CANCELED: JobStatus.JOB_CANCELLED,
        rs.job.DONE: JobStatus.JOB_COMPLETED,
        rs.job.FAILED: JobStatus.JOB_ERROR,
    }

    def __init__(self, command='', protocol='', host="localhost", **kwargs):
        super(SagaAdaptor, self).__init__(command, protocol, host, **kwargs)
        self._context = None

    @property
    def context(self):
        """ Create / initialize Saga-python session context """
        return self._context

    @property
    def session(self):
        if not self._session:
            session = rs.Session()
            session.add_context(self.context)
            logger.info("New session [--%s--]" % session)
            self._session = session
        return self._session

    def _connect(self):
        try:
            logger.debug('Connection to %s', self.saga_host)
            self.connector = self._init_service()
            self._connected = self.connector is not None and self.connector.valid and self.connector.session is not None
            logger.debug('Connected to %s', self.saga_host)
        except rs.SagaException as exc:
            self._connected = False
            # logger.exception(exc.message)
            raise exceptions.AdaptorConnectException(exc.message)

    def job_work_dir(self, job, mode=rs.filesystem.READ):
        return job.working_dir

    @property
    def available(self):
        try:
            service = self._init_service()
            self.connect()
        except (rs.SagaException, AssertionError, BaseException) as e:
            raise exceptions.AdaptorNotAvailableException(e)
        return service.valid

    def connexion_string(self):
        return self.saga_host

    @property
    def saga_host(self):
        """ Construct Saga-python adapter uri scheme """
        return '%s://%s' % (self.protocol, self.host)

    def _init_service(self):
        return rs.job.Service(self.saga_host)

    def _disconnect(self):
        logger.debug('Disconnect')
        self.connector.close()
        self.connector = None
        self._connected = False
        self._context = None

    def _prepare_job(self, job):
        # Nothing to do here
        job.logger.info('Nothing to prepare, we are local')
        return job

    def _run_job(self, job):
        """
        Launch the job with current parameters from associated history
        """
        try:
            job.logger.debug('Creating job descriptor')
            jd_dict = self._job_description(job)
            jd = rs.job.Description()
            for key in jd_dict.keys():
                setattr(jd, key, jd_dict[key])
            new_job = self.connector.create_job(jd)
            new_job.run()
            job.logger.debug('Job Descriptor %s', jd)
            job.remote_job_id = new_job.get_id()
            job.logger.debug('New saga job %s [id:%s]', new_job, new_job.get_id())
            return job
        except rs.SagaException as exc:
            raise exceptions.AdaptorJobException(exc.message)

    def _cancel_job(self, job):
        """
        Jobs Cancel if connector is available
        """
        try:
            the_job = self.connector.get_job(str(job.remote_job_id))
            the_job.cancel()
            return job
        except rs.SagaException as exc:
            raise exceptions.AdaptorJobException(exc.message)

    def _job_status(self, job):
        try:
            the_job = self.connector.get_job(str(job.remote_job_id))
            return the_job.state
        except rs.SagaException as exc:
            raise exceptions.AdaptorJobException(exc.message)

    def _job_description(self, job):
        desc = dict(working_directory=job.working_dir,
                    executable=self.command,
                    arguments=job.command_line_arguments,
                    output=job.stdout,
                    error=job.stderr)
        return desc

    def _job_results(self, job):
        try:
            saga_job = self.connector.get_job(str(job.remote_job_id))
            job.results_available = True
            job.exit_code = saga_job.exit_code
            return job
        except rs.SagaException as exc:
            raise exceptions.AdaptorJobException(exc.message)

    def _job_run_details(self, job):
        remote_job = self.connector.get_job(str(job.remote_job_id))
        date_created = remote_job.created if remote_job.created else ""
        date_started = remote_job.started if remote_job.started else ""
        date_finished = remote_job.finished if remote_job.finished else ""
        details = JobRunDetails(job.id, str(job.slug), remote_job.id, remote_job.name,
                                remote_job.exit_code,
                                date_created,
                                date_started,
                                date_finished,
                                remote_job.execution_hosts)
        return details

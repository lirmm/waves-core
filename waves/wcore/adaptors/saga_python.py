from __future__ import unicode_literals

import saga
from waves.wcore.adaptors import const, JobAdaptor
from waves.wcore.adaptors import exceptions
import logging

logger = logging.getLogger(__name__)


class SagaAdaptor(JobAdaptor):
    """
    Main Saga-python WAVES adaptor container

    """
    _session = None
    _states_map = {
        saga.job.UNKNOWN: const.JOB_UNDEFINED,
        saga.job.NEW: const.JOB_QUEUED,
        saga.job.PENDING: const.JOB_QUEUED,
        saga.job.RUNNING: const.JOB_RUNNING,
        saga.job.SUSPENDED: const.JOB_SUSPENDED,
        saga.job.CANCELED: const.JOB_CANCELLED,
        saga.job.DONE: const.JOB_COMPLETED,
        saga.job.FAILED: const.JOB_ERROR,
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
            session = saga.Session()
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
        except saga.SagaException as exc:
            self._connected = False
            # logger.exception(exc.message)
            raise exceptions.AdaptorConnectException(exc.message)

    def job_work_dir(self, job, mode=saga.filesystem.READ):
        return job.working_dir

    @property
    def available(self):
        try:
            service = self._init_service()
        except saga.NoSuccess as e:
            raise exceptions.AdaptorNotAvailableException(e.message)
        return service.valid

    def connexion_string(self):
        return self.saga_host

    @property
    def saga_host(self):
        """ Construct Saga-python adaptor uri scheme """
        return '%s://%s' % (self.protocol, self.host)

    def _init_service(self):
        return saga.job.Service(self.saga_host)

    def _disconnect(self):
        logger.debug('Disconnect')
        self.connector.close()
        self.connector = None
        self._connected = False
        self._context = None

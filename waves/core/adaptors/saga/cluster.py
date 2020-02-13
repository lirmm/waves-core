from waves.core.adaptors.saga.shell import SshKeyShellAdaptor, SshShellAdaptor
from waves.core.adaptors.saga.base import SagaAdaptor


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

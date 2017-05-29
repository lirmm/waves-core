from __future__ import unicode_literals

from waves.adaptors.core.shell import LocalShellAdaptor, SshKeyShellAdaptor, SshShellAdaptor


class LocalClusterAdaptor(LocalShellAdaptor):
    """
    Encapsulate some of Saga-python adaptors for common cluster calculation devices onto WAVES adaptor logic
    """
    NOT_AVAILABLE_MESSAGE = "A valid local %s cluster is needed to run this tests"

    name = 'Local cluster'
    #: For cluster based remote runners, set up default cluster job queue (if any)
    queue = ''
    #: List of currently implemented remote cluster schemes
    protocol = ''
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



    @property
    def init_params(self):
        """ Base init_params for Cluster JobAdaptor """
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

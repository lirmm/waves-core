from __future__ import unicode_literals

import logging
import time
from os.path import join, dirname, realpath, isfile

from django.utils.timezone import localtime

import waves.adaptors.const
from waves.adaptors.loader import AdaptorLoader
from waves.models import Runner, Service
from waves.settings import waves_settings

logger = logging.getLogger(__name__)


def assertion_tracker(func):
    def method_wrapper(method):
        def wrapped_method(test, *args, **kwargs):
            return method(test, *args, **kwargs)

        # Must preserve method name so nose can detect and report tests by
        # name.
        wrapped_method.__name__ = method.__name__
        return wrapped_method

    return method_wrapper


def get_sample_dir():
    return join(dirname(dirname(realpath(__file__))), 'data', 'sample')


def run_job_workflow(job):
    """ Run a full complete job workflow, you should call this method catching "AssertionError" to get
    error messages in your tests
    """
    logger.info('Starting workflow process for job %s', job)
    assert (job.job_history.count() == 1), "Wrong job history count %s (expected 1)" % job.job_history.count()
    job.run_prepare()
    time.sleep(3)
    assert (job.status == waves.adaptors.const.JOB_PREPARED), \
        "Wrong job status %s (expected %s) " % (job.status, waves.adaptors.const.JOB_PREPARED)
    job.run_launch()
    time.sleep(3)
    logger.debug('Remote Job ID %s', job.remote_job_id)
    assert (job.status == waves.adaptors.const.JOB_QUEUED), \
        "Wrong job status %s (expected %s) " % (job.status, waves.adaptors.const.JOB_QUEUED)
    for ix in range(100):
        job_state = job.run_status()
        logger.info(u'Current job state (%i) : %s ', ix, job.get_status_display())
        if job_state >= waves.adaptors.const.JOB_COMPLETED:
            logger.info('Job state ended to %s ', job.get_status_display())
            break
        time.sleep(3)
    if job.status in (waves.adaptors.const.JOB_COMPLETED, waves.adaptors.const.JOB_TERMINATED):
        # Get job run details
        job.run_details()
        time.sleep(3)
        history = job.job_history.first()
        logger.debug("History timestamp %s", localtime(history.timestamp))
        logger.debug("Job status timestamp %s", job.status_time)
        assert job.results_available, "Job results are not available"
        for output_job in job.outputs.all():
            # TODO reactivate job output verification as soon as possible
            if not isfile(output_job.file_path):
                logger.warning("Job <<%s>> did not output expected %s (test_data/jobs/%s/) ",
                               job.title, output_job.value, job.slug)

            assert (isfile(output_job.file_path)), "Job outut file does not exists %s"  % output_job.file_path
            logger.info("Expected output file: %s ", output_job.file_path)
        assert (job.status >= waves.adaptors.const.JOB_COMPLETED)
    else:
        logger.warn('problem with job status %s', job.get_status_display())
        return False
    return True


def create_test_file(path, index):
    import os
    full_path = os.path.join(waves_settings.JOB_DIR, '_' + str(index) + '_' + path)
    f = open(full_path, 'w')
    f.write('sample content for input file %s' % ('_' + str(index) + '_' + path))
    f.close()
    f = open(full_path, 'rb')
    return f


def create_runners():
    """ Create base models from all Current implementation parameters """
    runners = []
    loader = AdaptorLoader()
    for adaptor in loader.get_adaptors():
        runners.append(Runner.objects.create(name="%s Runner" % adaptor.name,
                                             clazz='.'.join([adaptor.__module__, adaptor.__class__.__name__])))
    return runners


def create_service_for_runners():
    """ initialize a empty service for each defined runner """
    services = []
    for runner in create_runners():
        srv = Service.objects.create(name="Service %s " % runner.name, runner=runner)
        services.append(srv)
    return services
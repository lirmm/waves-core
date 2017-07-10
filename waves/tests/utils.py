from __future__ import unicode_literals

import logging
import shutil

import time
from os.path import join, dirname, realpath, isfile, basename

from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import localtime

import waves.adaptors.const
from waves.adaptors.loader import AdaptorLoader
from waves.models import *
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


def create_base_job(title="Sample Empty Job -- Test"):
    job = Job.objects.create(title=title)
    return job


def create_cp_job(source_file):
    job = create_base_job('Sample CP job')
    shutil.copy(source_file, job.working_dir)
    job.inputs = [JobInput.objects.create(label="File To copy", name='source',
                                          value=basename(source_file), param_type=AParam.TYPE_FILE, job=job),
                  JobInput.objects.create(label="Destination Dir", name="dest",
                                          value='dest_copy.txt', param_type=AParam.TYPE_TEXT, job=job)]
    job.outputs = [JobOutput.objects.create(_name='Copied File', name='dest', value=job.inputs[1].value, job=job)]
    return job


class TestJobWorkflowMixin(object):
    def run_job_workflow(self, job):
        """ Run a full complete job workflow, you should call this method catching "AssertionError" to get
        error messages in your tests
        """
        logger.info('Starting workflow process for job %s', job)
        self.assertTrue(job.job_history.count() == 1,
                        "Wrong job history count %s (expected 1)" % job.job_history.count())
        job.run_prepare()
        time.sleep(3)
        self.assertTrue(job.status == waves.adaptors.const.JOB_PREPARED,
                        "Wrong job status %s (expected %s) " % (job.status, waves.adaptors.const.JOB_PREPARED))
        job.run_launch()
        time.sleep(3)
        logger.debug('Remote Job ID %s', job.remote_job_id)
        self.assertTrue(job.status == waves.adaptors.const.JOB_QUEUED,
                        "Wrong job status %s (expected %s) " % (job.status, waves.adaptors.const.JOB_QUEUED))
        for ix in range(100):
            job_state = job.run_status()
            logger.info(u'Current job state (%i) : %s ', ix, job.get_status_display())
            if job_state >= waves.adaptors.const.JOB_COMPLETED:
                logger.info('Job state ended to %s ', job.get_status_display())
                if job_state == waves.adaptors.const.JOB_ERROR:
                    self.fails('Job should not be in error')
                break
            time.sleep(3)
        if job.status in (waves.adaptors.const.JOB_COMPLETED, waves.adaptors.const.JOB_TERMINATED):
            # Get job run details
            job.run_details()
            time.sleep(3)
            history = job.job_history.first()
            logger.debug("History timestamp %s", localtime(history.timestamp))
            logger.debug("Job status timestamp %s", job.status_time)
            self.assertTrue(job.results_available, "Job results are not available")
            for output_job in job.outputs.all():
                # TODO reactivate job output verification as soon as possible
                if not isfile(output_job.file_path):
                    logger.warning("Job <<%s>> did not output expected %s (test_data/jobs/%s/) ",
                                   job.title, output_job.value, job.slug)

                logger.info("Expected output file: %s ", output_job.file_path)
                self.assertTrue(isfile(output_job.file_path), "Job outut file does not exists %s" % output_job.file_path)
            self.assertTrue(job.status == waves.adaptors.const.JOB_TERMINATED)
        else:
            logger.warn('problem with job status %s', job.get_status_display())
            return False
        return True


def create_test_file(path, index):
    import os
    full_path = os.path.join(waves_settings.JOB_BASE_DIR, '_' + str(index) + '_' + path)
    f = open(full_path, 'w')
    f.write('sample content for input file %s' % ('_' + str(index) + '_' + path))
    f.close()
    f = open(full_path, 'rb')
    return f


def create_runners():
    """ Create base models from all Current implementation parameters """
    runners = []
    loader = AdaptorLoader
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


def get_sample():
    return join(dirname(__file__), 'samples', 'test_copy.txt')


def get_copy():
    return 'dest_copy.txt'


def sample_runner(runner_impl):
    """
    Return a new adaptor model instance from adaptor class object
    Args:
        runner_impl: a JobRunnerAdaptor object
    Returns:
        Runner model instance
    """
    runner_model = Runner.objects.create(name=runner_impl.__class__.__name__,
                                         description='SubmissionSample Runner %s' % runner_impl.__class__.__name__,
                                         clazz='%s.%s' % (runner_impl.__module__, runner_impl.__class__.__name__))
    object_ctype = ContentType.objects.get_for_model(runner_model)
    for name, value in runner_impl.init_params.items():
        AdaptorInitParam.objects.update_or_create(name=name, content_type=object_ctype, object_id=runner_model.pk,
                                                  defaults={'value': value})
    return runner_model


def sample_job(service):
    """
    Return a new Job model instance for service
    Args:
        service: a Service model instance
    Returns:
        Job model instance
    """
    job = Job.objects.create(title='SubmissionSample Job', submission=service.submissions.first())
    srv_submission = service.default_submission
    for srv_input in srv_submission.submission_inputs.all():
        job.job_inputs.add(JobInput.objects.create(srv_input=srv_input, job=job, value="fake_value"))
    return job


def sample_service(runner, init_params=None):
    """ Create a sample service for this runner """
    service = Service.objects.create(name='Sample Service', runner=runner)
    if init_params:
        for name, value in init_params:
            service.run_params.add(ServiceRunParam.objects.create(name=name, value=value))
    sub = Submission.objects.create(name="Default Submission", service=service)
    service.submissions.add(sub)

    return service

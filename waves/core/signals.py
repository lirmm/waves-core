"""
WAVES Automated models signals handlers
"""
from __future__ import unicode_literals

import os
import shutil

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from waves.core.models.adaptors import AdaptorInitParam, HasAdaptorClazzMixin
from waves.core.models.base import ApiModel
from waves.core.models.inputs import *
from waves.core.models.jobs import Job, JobOutput
from waves.core.models.runners import *
from waves.core.models.services import *
from waves.core.models.submissions import *
from waves.core.models.samples import *
from waves.core.utils import get_all_subclasses


@receiver(pre_save, sender=Job)
def job_pre_save_handler(sender, instance, **kwargs):
    """ job presave handler """
    if not instance.message:
        instance.message = instance.get_status_display()


@receiver(post_save, sender=Job)
def job_post_save_handler(sender, instance, created, **kwargs):
    """ job post save handler """
    if not kwargs.get('raw', False):
        if created:
            # create job working dirs locally
            instance.make_job_dirs()
            instance.create_default_outputs()
            instance.job_history.create(message="Job Defaults created", status=instance.status)


@receiver(post_delete, sender=Job)
def job_post_delete_handler(sender, instance, **kwargs):
    """ post delete job handler """
    instance.delete_job_dirs()


@receiver(post_delete, sender=Service)
def service_post_delete_handler(sender, instance, **kwargs):
    """ service post delete handler """
    if os.path.exists(instance.sample_dir):
        shutil.rmtree(instance.sample_dir)


@receiver(post_save, sender=Service)
def service_post_save_handler(sender, instance, created, **kwargs):
    """ service post delete handler """
    if created and not kwargs.get('raw', False):
        instance.submissions.add(Submission.objects.create(name='default', service=instance))


@receiver(pre_save, sender=Submission)
def submission_pre_save_handler(sender, instance, **kwargs):
    """ submission pre save """
    if not instance.name:
        instance.name = instance.service.name


@receiver(post_save, sender=Submission)
def submission_post_save_handler(sender, instance, created, **kwargs):
    """ submission pre save """
    if created and not kwargs.get('raw', False):
        instance.exit_codes.add(SubmissionExitCode.objects.create(submission=instance, exit_code=0,
                                                                  message='Process exit normally'))
        instance.exit_codes.add(SubmissionExitCode.objects.create(submission=instance, exit_code=1,
                                                                  is_error=True,
                                                                  message='Process exit error'))


@receiver(post_delete, sender=FileInputSample)
def service_sample_post_delete_handler(sender, instance, **kwargs):
    """ SubmissionSample delete handler """
    if instance.file:
        instance.file.delete()


@receiver(post_delete, sender=FileInput)
def service_input_post_delete_handler(sender, instance, **kwargs):
    """ SubmissionParam post delete handler"""
    if instance.input_samples.count() > 0:
        for sample in instance.input_samples.all():
            sample.file.delete()


@receiver(post_save, sender=Runner)
def runner_post_save_handler(sender, instance, created, **kwargs):
    if created or instance.config_changed:
        instance.set_run_params_defaults()


@receiver(post_save, sender=HasAdaptorClazzMixin)
def adaptor_mixin_post_save_handler(sender, instance, created, **kwargs):
    if not kwargs.get('raw', False) and (instance.config_changed or created):
        instance.set_run_params_defaults()


for subclass in get_all_subclasses(HasAdaptorClazzMixin):
    if not subclass._meta.abstract:
        post_save.connect(adaptor_mixin_post_save_handler, subclass)


@receiver(pre_save, sender=AdaptorInitParam)
def adaptor_param_pre_save_handler(sender, instance, **kwargs):
    """ Runner param pre save handler """
    if instance.config_changed and instance.crypt and instance.value:
        from waves.core.utils.encrypt import Encrypt
        instance.value = Encrypt.encrypt(instance.value)

for subclass in get_all_subclasses(AdaptorInitParam):
    if not subclass._meta.abstract:
        pre_save.connect(adaptor_param_pre_save_handler, subclass)


@receiver(pre_save, sender=ApiModel)
def api_able_pre_save_handler(sender, instance, **kwargs):
    """ Any ApiModel model object setup api_name if not already set in object data """
    if not instance.api_name or instance.api_name == '':
        instance.api_name = instance.create_api_name()
        exists = instance.duplicate_api_name()
        if exists.count() > 0:
            instance.api_name += '_' + str(exists.count())


@receiver(post_save, sender=JobOutput)
def job_output_post_save_handler(sender, instance, created, **kwargs):
    """ Job Output post save handler """
    pass
    """
    if created and instance.value and not kwargs.get('raw', False):
        # Create empty file for expected outputs
        open(join(instance.job.working_dir, instance.value), 'a').close()
    """

# Connect all ApiModel subclass to pre_save_handler
for subclass in get_all_subclasses(ApiModel): #.__subclasses__():
    pre_save.connect(api_able_pre_save_handler, subclass)



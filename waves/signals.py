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
import os
import shutil

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from waves.core.utils import get_all_subclasses
from waves.core.utils import random_job_title
from waves.models import AdaptorInitParam, HasAdaptorClazzMixin, ServiceBinaryFile
from waves.models import FileInputSample, FileInput, Job, JobOutput, Runner, Service, Submission, SubmissionExitCode
from waves.models.base import ApiModel


@receiver(pre_save, sender=Job)
def job_pre_save_handler(sender, instance, **kwargs):
    """ job presave handler """
    if instance.submission:
        if not instance.service:
            instance.service = instance.submission.service.name
        if not instance.notify:
            instance.notify = instance.submission.service.email_on
    if not instance.title:
        instance.title = random_job_title()
    if not instance.message:
        # TODO CHECK usage
        instance.message = instance.get_status_display()


@receiver(post_save, sender=Job)
def job_post_save_handler(sender, instance, created, **kwargs):
    """ job post save handler """
    if not kwargs.get('raw', False) and created:
        # create job working dirs locally
        instance.make_job_dirs()
        instance.create_non_editable_inputs()
        instance.create_default_outputs()
        instance.job_history.create(message="Job defaults created", status=instance.status)


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
    if created and not kwargs.get('raw', False) and instance.submissions.count() == 0:
        instance.submissions.add(Submission.objects.create(name='default', service=instance))
    if not os.path.isdir(instance.sample_dir):
        os.makedirs(instance.sample_dir, mode=0o775)


@receiver(pre_save, sender=Submission)
def submission_pre_save_handler(sender, instance, **kwargs):
    """ submission pre save """
    if not instance.name:
        instance.name = 'sub_' + instance.service.name


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
    if created:  # or instance.config_changed:
        instance.set_defaults()


@receiver(post_save, sender=HasAdaptorClazzMixin)
def adaptor_mixin_post_save_handler(sender, instance, created, **kwargs):
    if not kwargs.get('raw', False) and (instance.config_changed or created):
        instance.set_defaults()


for subclass in get_all_subclasses(HasAdaptorClazzMixin):
    # noinspection PyProtectedMember
    if not subclass._meta.abstract:
        post_save.connect(adaptor_mixin_post_save_handler, subclass)


@receiver(pre_save, sender=AdaptorInitParam)
def adaptor_param_pre_save_handler(sender, instance, **kwargs):
    """ Runner param pre save handler """
    if instance.config_changed and instance.name == "password" and instance.value:
        from waves.core.utils import Encrypt
        instance.crypt = True
        instance.value = Encrypt.encrypt(instance.value)


for subclass in get_all_subclasses(AdaptorInitParam):
    # noinspection PyProtectedMember
    if not subclass._meta.abstract:
        pre_save.connect(adaptor_param_pre_save_handler, subclass)


@receiver(pre_save, sender=ApiModel)
def api_able_pre_save_handler(sender, instance, **kwargs):
    """ Any ApiModel model object setup api_name if not already set in object data """
    if not instance.api_name or instance.api_name == '':
        # noinspection PyProtectedMember
        instance.api_name = instance._create_api_name()
    if not kwargs.get('raw', False):
        exists = instance.duplicate_api_name(instance.api_name).count()
        if exists > 0:
            deb = exists + 1
            while instance.duplicate_api_name(api_name='%s_%s' % (instance.api_name, deb)).count() > 0:
                deb += 1
            instance.api_name = "%s_%s" % (instance.api_name, deb)


@receiver(post_save, sender=JobOutput)
def job_output_post_save_handler(sender, instance, created, **kwargs):
    """ Job Output post save handler """
    pass
    # TODO check code obsolescence
    """
    if created and instance.value and not kwargs.get('raw', False):
        # Create empty file for expected outputs
        open(join(instance.job.working_dir, instance.value), 'a').close()
    """


# Connect all ApiModel subclass to pre_save_handler
for subclass in get_all_subclasses(ApiModel):  # .__subclasses__():
    pre_save.connect(api_able_pre_save_handler, subclass)

for subclass in get_all_subclasses(Job):
    post_save.connect(job_post_save_handler, subclass)


@receiver(post_delete, sender=ServiceBinaryFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.binary:
        dir_name = os.path.dirname(instance.binary.path)
        if os.path.isfile(instance.binary.path):
            os.remove(instance.binary.path)
        if not os.listdir(dir_name):
            os.rmdir(dir_name)


@receiver(pre_save, sender=ServiceBinaryFile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = ServiceBinaryFile.objects.get(pk=instance.pk).binary
    except ServiceBinaryFile.DoesNotExist:
        return False

    new_file = instance.binary
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)

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

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers as rest_serializer

from waves.core.import_export import BaseSerializer, RelatedSerializerMixin
from waves.api.current import serializers as api_serializers
from waves.core.import_export import serializers
from waves.models import Submission, Service
from waves.models import SubmissionExitCode, SubmissionOutput, SubmissionRunParam
from waves.models import AParam
from waves.models import Runner

__all__ = ['ServiceSubmissionSerializer', 'ExitCodeSerializer', 'ServiceSerializer']


class ServiceInputSerializer(BaseSerializer, RelatedSerializerMixin, serializers.InputSerializer):
    """ Serialize a basic service input with its dependents parameters"""

    class Meta:
        model = AParam
        fields = ('label', 'name', 'default', 'type', 'mandatory', 'help_text', 'multiple',)  # 'dependents_inputs',)

    # TODO reactivate dependent inputs serialzation
    # dependent_inputs = ServiceInputSerializer(many=True, required=False)

    def create(self, validated_data):
        dependent_inputs = validated_data.pop('dependents_inputs')
        srv_input = AParam.objects.create(**validated_data)
        self.create_related(foreign={'parent': srv_input},
                            serializer=ServiceInputSerializer,
                            datas=dependent_inputs)
        return srv_input


class ServiceSubmissionSerializer(BaseSerializer, serializers.ServiceSubmissionSerializer, RelatedSerializerMixin):
    """ Service Submission export / import """

    class Meta:
        model = Submission
        fields = ('api_name', 'order', 'name', 'availability', 'submission_inputs', 'export_submission_inputs')

    export_submission_inputs = ServiceInputSerializer(many=True, required=False, source="root_inputs", read_only=True)
    submission_inputs = ServiceInputSerializer(many=True, required=False, write_only=True, source="inputs")

    def create(self, validated_data):
        submission_inputs = validated_data.pop('export_submission_inputs', [])
        # validated_data['api_name'] = validated_data.get('service').api_name
        submission = Submission.objects.create(**validated_data)
        self.create_related(foreign={'service': submission}, serializer=ServiceInputSerializer, datas=submission_inputs)
        return submission


class ExitCodeSerializer(BaseSerializer):
    """ ExitCode export / import """

    class Meta:
        model = SubmissionExitCode
        fields = ('exit_code', 'message')


class SubmissionOutputSerializer(BaseSerializer):
    class Meta:
        model = Submission
        fields = ('api_name',)

    def create(self, validated_data):
        return Submission(api_name=validated_data.get('api_name'))


class ServiceOutputSerializer(BaseSerializer):
    class Meta:
        model = SubmissionOutput
        fields = ('order', 'name', 'from_input', 'description',
                  'short_description', 'from_input', 'file_pattern')

    def create(self, validated_data):
        # retrieve related input
        submission_from = validated_data.pop('from_input_submission')
        service = validated_data['service']
        obj = super(ServiceOutputSerializer, self).create(validated_data)
        for sub in submission_from:
            submit = service.submissions.filter(api_name=sub['submission']['api_name']).first()
            srv_input = submit.inputs.filter(name=sub['srv_input']['name']).first()
            output_submission = SubmissionOutput.objects.create(srv_input=srv_input,
                                                                submission=submit,
                                                                srv_output=obj)
            obj.from_input_submission.add(output_submission)
        return obj


class ServiceTmpSerializer(BaseSerializer):
    class Meta:
        model = Service
        fields = ('name',)


class ServiceRunnerParamSerializer(BaseSerializer):
    class Meta:
        model = SubmissionRunParam
        fields = ('param', '_value', 'service')

    param = api_serializers.RunnerParamSerializer(many=False, required=False)
    service = ServiceTmpSerializer(required=False)

    def create(self, validated_data):
        service = validated_data['service']
        param_dict = validated_data.pop('param')
        value = validated_data.pop('_value')
        param = service.runner.runner_run_params.get(name=param_dict['name'])
        obj, created = SubmissionRunParam.objects.update_or_create(defaults={'_value': value},
                                                                   param=param, service=service)
        return obj


class ServiceSerializer(BaseSerializer, api_serializers.ServiceSerializer, RelatedSerializerMixin):
    """ Service export / import """

    class Meta:
        model = Service
        fields = ('name', 'db_version', 'description', 'short_description', 'runner',
                  'srv_run_params', 'submissions', 'service_outputs', 'exit_codes')

    db_version = rest_serializer.SerializerMethodField()
    submissions = ServiceSubmissionSerializer(many=True, required=False)
    exit_codes = ExitCodeSerializer(many=True, required=False)
    service_outputs = ServiceOutputSerializer(many=True, required=False)
    runner = api_serializers.RunnerSerializer(many=False, required=False)
    srv_run_params = ServiceRunnerParamSerializer(many=True, required=False)

    def __init__(self, *args, **kwargs):
        self.skip_runner = kwargs.pop('skip_run', False)
        super(ServiceSerializer, self).__init__(*args, **kwargs)

    @transaction.atomic
    def create(self, validated_data):
        """ Create a new service from submitted data"""
        submissions = validated_data.pop('submissions', [])
        outputs = validated_data.pop('service_outputs', [])
        ext_codes = validated_data.pop('exit_codes', [])
        runner = validated_data.pop('runner', [])
        srv_run_params = validated_data.pop('srv_run_params', [])
        if not self.skip_runner:
            try:
                run_on = Runner.objects.filter(clazz=runner['clazz']).first()
            except ObjectDoesNotExist:
                srv = api_serializers.RunnerSerializer(data=runner)
                if srv.is_valid():
                    run_on = srv.save()
                else:
                    run_on = None
        else:
            run_on = None
        srv_object = Service.objects.create(**validated_data)
        srv_object.runner = run_on
        srv_object.save()
        if not self.skip_runner:
            s_run_p = ServiceRunnerParamSerializer(data=srv_run_params, many=True)
            if s_run_p.is_valid():
                s_run_p.save(service=srv_object)
        srv_object.submissions = self.create_related(foreign={'service': srv_object},
                                                     serializer=ServiceSubmissionSerializer, datas=submissions)
        srv_object.service_outputs = self.create_related(foreign={'service': srv_object},
                                                         serializer=ServiceOutputSerializer, datas=outputs)
        srv_object.exit_codes = self.create_related(foreign={'service': srv_object},
                                                    serializer=ExitCodeSerializer, datas=ext_codes)
        return srv_object

    def get_db_version(self, obj):
        from waves.settings import waves_settings
        return waves_settings.DB_VERSION

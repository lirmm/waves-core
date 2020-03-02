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
from django.db import transaction
from rest_framework import serializers

from waves.models import Runner, AdaptorInitParam
from .base import RelatedSerializerMixin

__all__ = ['RunnerParamSerializer', 'RunnerSerializer']


class RunnerParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptorInitParam
        fields = ('name', 'value', 'prevent_override')

    def to_representation(self, instance):
        repre = super(RunnerParamSerializer, self).to_representation(instance)
        if instance.name == 'password' or instance.crypt:
            repre['value'] = "xxxxxx"
        return repre


class RunnerSerializer(serializers.ModelSerializer, RelatedSerializerMixin):
    class Meta:
        model = Runner
        fields = ('name', 'clazz', 'runner_params')

    runner_params = RunnerParamSerializer(many=True, source='adaptor_params')

    @transaction.atomic
    def create(self, validated_data):
        runner_params = validated_data.pop('runner_params')
        runner = Runner.objects.create(**validated_data)
        runner.runner_run_params.all().delete()
        runner.runner_run_params = self.create_related(foreign={'runner': runner},
                                                       serializer=RunnerParamSerializer,
                                                       datas=runner_params)
        return runner
